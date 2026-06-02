import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.game import Game
from app.models.journal import GameRating, SessionLog
from app.models.library import LibraryEntry, LibraryStatus
from app.models.recommendation import (
    Recommendation,
    RecommendationItem,
    RecommendationKind,
    RecommendationStatus,
)
from app.services.llm_provider import LLMProviderError, get_default_llm_provider
from app.services import kv_store
from app.services.steam_import_service import (
    _best_by_popularity,
    _score_candidate as _score_title_match,
    normalize_game_title,
)

_STATUS_WEIGHTS: dict[LibraryStatus, float] = {
    LibraryStatus.COMPLETED: 4.0,
    LibraryStatus.PLAYING: 3.0,
    LibraryStatus.REPLAYING: 3.0,
    LibraryStatus.BACKLOG: 1.5,
    LibraryStatus.WISHLIST: 0.75,
}
_CACHE_TTL = timedelta(hours=settings.AI_PICKS_CACHE_HOURS)
_FUZZY_MATCH_THRESHOLD = 92.0


class CompactTasteSummary(BaseModel):
    top_genres: list[str] = Field(default_factory=list)
    top_tags: list[str] = Field(default_factory=list)
    top_platforms: list[str] = Field(default_factory=list)
    avoid_tags: list[str] = Field(default_factory=list)
    preferred_eras: list[str] = Field(default_factory=list)
    preferred_length: str = "medium"
    pace: str = "mixed"
    challenge: str = "moderate"
    story_vs_gameplay: str = "balanced"
    favorite_games: list[str] = Field(default_factory=list)
    disliked_games: list[str] = Field(default_factory=list)
    review_snippets: list[str] = Field(default_factory=list)
    session_note_snippets: list[str] = Field(default_factory=list)
    common_emotions: list[str] = Field(default_factory=list)
    facet_preferences: dict[str, float] = Field(default_factory=dict)


class TasteDossier(BaseModel):
    preferred_genres: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)
    preferred_platforms: list[str] = Field(default_factory=list)
    avoid_tags: list[str] = Field(default_factory=list)
    preferred_eras: list[str] = Field(default_factory=list)
    length_preference: str = "medium"
    pace: str = "mixed"
    challenge: str = "moderate"
    story_vs_gameplay: str = "balanced"
    anchor_games: list[str] = Field(default_factory=list)
    taste_summary: str


class AIPickCandidate(BaseModel):
    title: str
    slug: str | None = None
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    because_you_liked: list[str] = Field(default_factory=list)


class AIPicksProposal(BaseModel):
    taste_summary: str
    candidates: list[AIPickCandidate]


@dataclass(frozen=True)
class ResolvedAIPick:
    candidate: AIPickCandidate
    game: Game
    match_confidence: float
    match_reason: str


@dataclass(frozen=True)
class DroppedAIPick:
    candidate: AIPickCandidate
    reason: str
    match_confidence: float | None = None
    matched_game_id: int | None = None


def _dossier_cache_key(user_id: int) -> str:
    """Build the Redis cache key for a user's generated taste dossier."""
    return f"ai_picks:dossier:{user_id}"


def _dirty_cache_key(user_id: int) -> str:
    """Build the Redis key used to mark a dossier as stale."""
    return f"ai_picks:dirty:{user_id}"


def _truncate(text: str | None, limit: int = 120) -> str:
    """Trim long user-provided text snippets for compact LLM prompts."""
    if not text:
        return ""
    trimmed = " ".join(text.split())
    if len(trimmed) <= limit:
        return trimmed
    return trimmed[: limit - 1].rstrip() + "…"


def _entry_weight(entry: LibraryEntry) -> float:
    """Return the weight a library entry should contribute to taste analysis."""
    if entry.rating is not None:
        return float(entry.rating)
    return _STATUS_WEIGHTS.get(entry.status, 2.0)


def _era_label(year: int | None) -> str | None:
    """Convert a release year into a decade label for taste clustering."""
    if not year:
        return None
    return f"{(year // 10) * 10}s"


def _length_bucket(hours: float | None) -> str:
    """Bucket a game length into a coarse label the LLM can reason about."""
    if hours is None:
        return "medium"
    if hours < 10:
        return "short"
    if hours < 30:
        return "medium"
    if hours < 60:
        return "long"
    return "epic"


def invalidate_ai_picks_cache(user_id: int) -> None:
    """Mark AI Picks as stale after library, rating, or journal changes."""
    try:
        ttl_seconds = max(int(_CACHE_TTL.total_seconds()), 60)
        kv_store.delete(_dossier_cache_key(user_id))
        kv_store.set_text(_dirty_cache_key(user_id), "1", ttl_seconds=ttl_seconds)
    except Exception:
        pass


def _clear_dirty_flag(user_id: int) -> None:
    """Clear the stale marker after a fresh AI Picks batch is generated."""
    try:
        kv_store.delete(_dirty_cache_key(user_id))
    except Exception:
        pass


def _is_dirty(user_id: int) -> bool:
    """Return whether the user's cached taste dossier should be regenerated."""
    try:
        return kv_store.exists(_dirty_cache_key(user_id))
    except Exception:
        return False


def _load_cached_dossier(user_id: int) -> TasteDossier | None:
    """Load a previously generated taste dossier from Redis, if available."""
    try:
        payload = kv_store.get_text(_dossier_cache_key(user_id))
        if not payload:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return TasteDossier.model_validate(json.loads(payload))
    except Exception:
        return None


def _store_cached_dossier(user_id: int, dossier: TasteDossier) -> None:
    """Persist a generated taste dossier to Redis for reuse within the TTL."""
    try:
        kv_store.set_text(
            _dossier_cache_key(user_id),
            json.dumps(dossier.model_dump()),
            ttl_seconds=int(_CACHE_TTL.total_seconds()),
        )
    except Exception:
        pass


def build_compact_taste_summary(user_id: int, db: Session) -> CompactTasteSummary:
    """
    Summarize all explicit player signals before the LLM turn.

    The compact summary blends library status, ratings, journal notes, and
    review text into a small structured object that is cheap to cache and safe
    to hand to the downstream Gemini dossier generator.
    """
    entries: list[LibraryEntry] = (
        db.query(LibraryEntry)
        .options(joinedload(LibraryEntry.game))
        .filter(LibraryEntry.user_id == user_id)
        .all()
    )
    ratings: list[GameRating] = (
        db.query(GameRating)
        .filter(GameRating.user_id == user_id)
        .all()
    )
    sessions: list[SessionLog] = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id)
        .options(joinedload(SessionLog.game))
        .order_by(SessionLog.started_at.desc())
        .all()
    )

    if not entries and not ratings and not sessions:
        raise ValueError("Add games, ratings, or journal activity before generating AI Picks.")

    genre_weights: dict[str, float] = defaultdict(float)
    tag_weights: dict[str, float] = defaultdict(float)
    platform_weights: dict[str, float] = defaultdict(float)
    avoid_tag_weights: dict[str, float] = defaultdict(float)
    era_weights: dict[str, float] = defaultdict(float)
    positive_games: list[tuple[float, str]] = []
    negative_games: list[tuple[float, str]] = []
    review_snippets: list[str] = []
    note_snippets: list[str] = []
    emotion_counts: Counter[str] = Counter()
    length_votes: list[str] = []

    for entry in entries:
        if not entry.game:
            continue
        game = entry.game
        weight = _entry_weight(entry)
        release_year = game.released.year if game.released else None
        length_hours = game.hltb_main_hours or (float(game.playtime) if game.playtime else None)
        is_negative_signal = entry.status == LibraryStatus.DROPPED or (
            entry.rating is not None and entry.rating <= 2.5
        )

        for tag in (game.tags or []):
            tag_name = tag.get("name")
            if not tag_name or tag.get("language", "eng") not in ("eng", ""):
                continue
            if is_negative_signal:
                avoid_tag_weights[tag_name] += 1.5
            elif weight >= 3.0:
                tag_weights[tag_name] += weight

        if is_negative_signal:
            negative_games.append((5.0 if entry.rating is None else 5.0 - entry.rating, game.name))
            if entry.review:
                review_snippets.append(_truncate(entry.review))
            continue

        for genre in (game.genres or []):
            genre_weights[genre["name"]] += weight
        for platform in (game.platforms or []):
            platform_name = platform.get("name")
            if platform_name:
                platform_weights[platform_name] += weight

        era = _era_label(release_year)
        if era and weight >= 3.0:
            era_weights[era] += weight
        if weight >= 3.0 and length_hours is not None:
            length_votes.append(_length_bucket(length_hours))

        if entry.rating is not None and entry.rating >= 4:
            positive_games.append((entry.rating, game.name))
        elif entry.status == LibraryStatus.COMPLETED:
            positive_games.append((weight, game.name))

        if entry.review:
            review_snippets.append(_truncate(entry.review))

    facet_values: dict[str, list[float]] = defaultdict(list)
    for rating in ratings:
        for field in ("story", "gameplay", "visuals", "soundtrack", "overall"):
            value = getattr(rating, field)
            if value is not None:
                facet_values[field].append(float(value))

    for session in sessions[:10]:
        if session.notes:
            note_snippets.append(_truncate(session.notes))
        for emotion in (session.emotions or []):
            emotion_counts[emotion] += 1

    facet_preferences = {
        field: round(sum(values) / len(values), 2)
        for field, values in facet_values.items()
        if values
    }

    preferred_length = "medium"
    if length_votes:
        preferred_length = Counter(length_votes).most_common(1)[0][0]

    story_avg = facet_preferences.get("story")
    gameplay_avg = facet_preferences.get("gameplay")
    if story_avg is not None and gameplay_avg is not None:
        if story_avg - gameplay_avg >= 0.75:
            svg = "story-heavy"
        elif gameplay_avg - story_avg >= 0.75:
            svg = "gameplay-heavy"
        else:
            svg = "balanced"
    else:
        svg = "balanced"

    pace = "mixed"
    challenge = "moderate"
    lower_tags = {name.lower() for name in tag_weights}
    if any(tag in lower_tags for tag in ("turn-based", "story rich", "choices matter", "atmospheric")):
        pace = "measured"
    if any(tag in lower_tags for tag in ("fast-paced", "arcade", "action-packed")):
        pace = "fast"
    if any(tag in lower_tags for tag in ("difficult", "souls-like", "precision platformer")):
        challenge = "high"
    if any(tag in lower_tags for tag in ("casual", "relaxing", "cozy")):
        challenge = "low"

    return CompactTasteSummary(
        top_genres=[name for name, _ in sorted(genre_weights.items(), key=lambda item: item[1], reverse=True)[:5]],
        top_tags=[name for name, _ in sorted(tag_weights.items(), key=lambda item: item[1], reverse=True)[:8]],
        top_platforms=[name for name, _ in sorted(platform_weights.items(), key=lambda item: item[1], reverse=True)[:4]],
        avoid_tags=[name for name, _ in sorted(avoid_tag_weights.items(), key=lambda item: item[1], reverse=True)[:6]],
        preferred_eras=[name for name, _ in sorted(era_weights.items(), key=lambda item: item[1], reverse=True)[:3]],
        preferred_length=preferred_length,
        pace=pace,
        challenge=challenge,
        story_vs_gameplay=svg,
        favorite_games=[name for _, name in sorted(positive_games, key=lambda item: item[0], reverse=True)[:5]],
        disliked_games=[name for _, name in sorted(negative_games, key=lambda item: item[0], reverse=True)[:3]],
        review_snippets=review_snippets[:4],
        session_note_snippets=note_snippets[:4],
        common_emotions=[name for name, _ in emotion_counts.most_common(4)],
        facet_preferences=facet_preferences,
    )


def build_taste_dossier(user_id: int, db: Session, *, force_refresh: bool = False) -> tuple[CompactTasteSummary, TasteDossier]:
    """
    Turn the compact player summary into the richer AI Picks dossier.

    The compact summary is always computed first so the service can validate
    the user's available taste signal, then the LLM expands that summary into a
    more expressive dossier used for candidate scoring and pick generation.
    """
    compact_summary = build_compact_taste_summary(user_id, db)
    if not force_refresh:
        cached = _load_cached_dossier(user_id)
        if cached is not None:
            return compact_summary, cached

    provider = get_default_llm_provider()
    dossier = provider.generate_structured(
        system_prompt=(
            "You are a careful game taste analyst. Summarize player taste from the structured evidence only. "
            "Do not invent games or preferences that are not supported by the evidence."
        ),
        user_prompt=(
            "Turn this compact player summary into a concise recommendation dossier.\n\n"
            f"{json.dumps(compact_summary.model_dump(), ensure_ascii=True)}"
        ),
        schema=TasteDossier,
    )
    _store_cached_dossier(user_id, dossier)
    return compact_summary, dossier


def _proposal_prompt(dossier: TasteDossier) -> str:
    """Format the taste dossier for LLM-native game proposal generation."""
    return (
        f"Recommend exactly {settings.AI_PICKS_MAX_CANDIDATES} real, commercially released video games for this player.\n"
        "Use exact game titles that are likely to exist in a RAWG-backed game catalog.\n"
        "Do not recommend franchises, DLC, demos, soundtracks, bundles, editions, mods, unreleased games, "
        "or vague series names. Prefer a mix of obvious strong fits and a few interesting discoveries.\n"
        "Each explanation should be concise, specific, and grounded in the taste dossier.\n\n"
        f"Taste dossier:\n{json.dumps(dossier.model_dump(), ensure_ascii=True)}"
    )


def _validate_proposal(proposal: AIPicksProposal) -> AIPicksProposal:
    """Reject malformed AI Picks proposal payloads before title resolution."""
    if not proposal.taste_summary.strip():
        raise ValueError("Missing taste summary from AI Picks response.")
    if not proposal.candidates:
        raise ValueError("AI Picks returned no candidate games.")
    for candidate in proposal.candidates:
        if not candidate.title.strip():
            raise ValueError("AI Picks returned a candidate with an empty title.")
        if not candidate.explanation.strip():
            raise ValueError("AI Picks returned a candidate with an empty explanation.")
    return proposal


def _generate_proposal_once(dossier: TasteDossier, *, stricter: bool = False) -> AIPicksProposal:
    """Ask Gemini for title-first AI Picks proposals."""
    provider = get_default_llm_provider()
    user_prompt = _proposal_prompt(dossier)
    if stricter:
        user_prompt += (
            "\n\nRepair mode: return only valid JSON, include exact standalone game titles, "
            "avoid DLC/editions/franchise names, and include no duplicate titles."
        )
    return provider.generate_structured(
        system_prompt=(
            "You are an expert game curator. Propose real games from the player's taste evidence. "
            "Return structured JSON only."
        ),
        user_prompt=user_prompt,
        schema=AIPicksProposal,
    )


def _normalized_slug(value: str | None) -> str:
    """Normalize an LLM-provided slug enough for exact slug lookup."""
    if not value:
        return ""
    return value.strip().lower()


def _resolve_candidate(
    candidate: AIPickCandidate,
    games: list[Game],
    exact_title_index: dict[str, list[Game]],
    slug_index: dict[str, Game],
) -> tuple[Game | None, float | None, str]:
    """Resolve one LLM-proposed title to a strict local Postgres game match."""
    slug = _normalized_slug(candidate.slug)
    if slug and slug in slug_index:
        return slug_index[slug], 100.0, "exact_slug"

    normalized_title = normalize_game_title(candidate.title)
    exact_matches = exact_title_index.get(normalized_title, [])
    if exact_matches:
        return _best_by_popularity(exact_matches), 100.0, "exact_title"

    best_game: Game | None = None
    best_score = 0.0
    for game in games:
        score = _score_title_match(candidate.title, game.name)
        if score > best_score:
            best_game = game
            best_score = score

    if best_game and best_score >= _FUZZY_MATCH_THRESHOLD:
        return best_game, round(best_score, 2), "fuzzy_title"
    if best_game:
        return None, round(best_score, 2), "low_confidence_match"
    return None, None, "not_found"


def resolve_ai_pick_candidates(
    user_id: int,
    proposal: AIPicksProposal,
    db: Session,
) -> tuple[list[ResolvedAIPick], list[DroppedAIPick]]:
    """
    Resolve LLM-proposed titles against the local catalog.

    Only resolved, unowned, non-duplicate games are eligible for storage. Missing
    Postgres rows are dropped because the UI needs the local Game metadata.
    """
    owned_game_ids = {
        entry.game_id
        for entry in db.query(LibraryEntry).filter(LibraryEntry.user_id == user_id).all()
    }
    games = db.query(Game).all()
    exact_title_index: dict[str, list[Game]] = {}
    slug_index: dict[str, Game] = {}
    for game in games:
        exact_title_index.setdefault(normalize_game_title(game.name), []).append(game)
        slug_index[game.slug.lower()] = game

    resolved: list[ResolvedAIPick] = []
    dropped: list[DroppedAIPick] = []
    seen_game_ids: set[int] = set()

    for candidate in proposal.candidates:
        game, match_confidence, match_reason = _resolve_candidate(candidate, games, exact_title_index, slug_index)
        if game is None:
            dropped.append(DroppedAIPick(candidate, match_reason, match_confidence))
            continue
        if game.id in owned_game_ids:
            dropped.append(DroppedAIPick(candidate, "owned", match_confidence, game.id))
            continue
        if game.id in seen_game_ids:
            dropped.append(DroppedAIPick(candidate, "duplicate", match_confidence, game.id))
            continue

        seen_game_ids.add(game.id)
        resolved.append(ResolvedAIPick(candidate, game, match_confidence or 100.0, match_reason))
        if len(resolved) >= settings.AI_PICKS_MAX_RESULTS:
            break

    return resolved, dropped


def generate_ai_picks_for_recommendation(recommendation_id: int, user_id: int, db: Session) -> Recommendation:
    """
    Populate a pending AI Picks recommendation with Postgres-resolved LLM proposals.

    This is the production path for the LLM-native recommendations surface: it
    gathers the user's taste dossier, asks the LLM for game titles, resolves
    them against the local catalog, stores the grounded result, and clears the
    stale marker.
    """
    recommendation = (
        db.query(Recommendation)
        .filter(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == user_id,
            Recommendation.kind == RecommendationKind.AI_PICKS,
        )
        .first()
    )
    if recommendation is None:
        raise ValueError(f"AI Picks batch {recommendation_id} not found.")

    compact_summary, dossier = build_taste_dossier(user_id, db)

    try:
        proposal = _validate_proposal(_generate_proposal_once(dossier, stricter=False))
    except (ValueError, LLMProviderError):
        proposal = _validate_proposal(_generate_proposal_once(dossier, stricter=True))

    resolved, dropped = resolve_ai_pick_candidates(user_id, proposal, db)
    if not resolved:
        recommendation.profile_snapshot = {
            "compact_summary": compact_summary.model_dump(),
            "taste_dossier": dossier.model_dump(),
            "raw_candidates": [candidate.model_dump() for candidate in proposal.candidates],
            "resolved_game_ids": [],
            "dropped_candidates": [
                {
                    "candidate": dropped_pick.candidate.model_dump(),
                    "reason": dropped_pick.reason,
                    "match_confidence": dropped_pick.match_confidence,
                    "matched_game_id": dropped_pick.matched_game_id,
                }
                for dropped_pick in dropped
            ],
        }
        recommendation.summary = "AI Picks could not match any suggested games to the local catalog."
        recommendation.model_name = settings.AI_PICKS_MODEL
        recommendation.status = RecommendationStatus.FAILED
        db.commit()
        raise ValueError("AI Picks could not match any suggested games to the local catalog.")

    recommendation.items.clear()
    recommendation.profile_snapshot = {
        "compact_summary": compact_summary.model_dump(),
        "taste_dossier": dossier.model_dump(),
        "raw_candidates": [candidate.model_dump() for candidate in proposal.candidates],
        "resolved_game_ids": [pick.game.id for pick in resolved],
        "dropped_candidates": [
            {
                "candidate": dropped_pick.candidate.model_dump(),
                "reason": dropped_pick.reason,
                "match_confidence": dropped_pick.match_confidence,
                "matched_game_id": dropped_pick.matched_game_id,
            }
            for dropped_pick in dropped
        ],
    }
    recommendation.summary = proposal.taste_summary
    recommendation.model_name = settings.AI_PICKS_MODEL
    recommendation.status = RecommendationStatus.READY
    recommendation.generated_at = datetime.now(timezone.utc)

    for rank, pick in enumerate(resolved, start=1):
        recommendation.items.append(
            RecommendationItem(
                game_id=pick.game.id,
                rank=rank,
                score=float(pick.candidate.confidence),
                explanation=pick.candidate.explanation.strip(),
                confidence=float(pick.candidate.confidence),
                because_you_liked=pick.candidate.because_you_liked or None,
            )
        )

    db.commit()
    db.refresh(recommendation)
    _clear_dirty_flag(user_id)
    return recommendation


def _latest_ai_picks_query(user_id: int, db: Session):
    """Return the newest AI Picks recommendation query for a user."""
    return (
        db.query(Recommendation)
        .options(joinedload(Recommendation.items).joinedload(RecommendationItem.game))
        .filter(
            Recommendation.user_id == user_id,
            Recommendation.kind == RecommendationKind.AI_PICKS,
        )
        .order_by(Recommendation.generated_at.desc())
    )


def _is_stale(recommendation: Recommendation | None, user_id: int) -> bool:
    """Decide whether the current AI Picks recommendation should be refreshed."""
    if recommendation is None:
        return True
    if recommendation.status != RecommendationStatus.READY:
        return True
    generated_at = recommendation.generated_at
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    if _is_dirty(user_id):
        return True
    return generated_at < (datetime.now(timezone.utc) - _CACHE_TTL)


def get_ai_picks_state(user_id: int, db: Session) -> dict[str, Any]:
    """
    Return the current AI Picks state for the UI.

    The payload includes the latest recommendation, whether it is stale, and
    whether the user can request a refresh.
    """
    recommendation = _latest_ai_picks_query(user_id, db).first()
    stale = _is_stale(recommendation, user_id)

    if recommendation is None:
        return {
            "recommendation": None,
            "is_stale": True,
            "can_refresh": True,
            "cache_hours": settings.AI_PICKS_CACHE_HOURS,
            "detail": "No AI Picks have been generated yet.",
        }

    detail = None
    if recommendation.status == RecommendationStatus.PENDING:
        detail = "AI Picks are being generated."
    elif recommendation.status == RecommendationStatus.FAILED:
        detail = recommendation.summary or "AI Picks could not be generated."
    elif stale:
        detail = "Your AI Picks are stale. Refresh to regenerate them."

    return {
        "recommendation": recommendation,
        "is_stale": stale,
        "can_refresh": recommendation.status != RecommendationStatus.PENDING,
        "cache_hours": settings.AI_PICKS_CACHE_HOURS,
        "detail": detail,
    }


def request_ai_picks_refresh(user_id: int, db: Session) -> tuple[Recommendation, bool]:
    """
    Create a pending AI Picks recommendation and signal whether to enqueue it.

    The API layer uses the boolean return value to decide whether a Celery job
    should be dispatched immediately. A user-initiated refresh always creates a
    new batch unless another refresh is already pending.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("AI Picks is not configured yet. Add GEMINI_API_KEY to enable it.")

    build_compact_taste_summary(user_id, db)

    latest = _latest_ai_picks_query(user_id, db).first()
    if latest is not None and latest.status == RecommendationStatus.PENDING:
        return latest, False

    recommendation = Recommendation(
        user_id=user_id,
        generated_at=datetime.now(timezone.utc),
        kind=RecommendationKind.AI_PICKS,
        status=RecommendationStatus.PENDING,
        model_name=settings.AI_PICKS_MODEL,
        summary="AI Picks are being generated.",
        profile_snapshot={},
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation, True
