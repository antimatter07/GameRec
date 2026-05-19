import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import redis as redis_lib
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

_STATUS_WEIGHTS: dict[LibraryStatus, float] = {
    LibraryStatus.COMPLETED: 4.0,
    LibraryStatus.PLAYING: 3.0,
    LibraryStatus.BACKLOG: 2.0,
    LibraryStatus.DROPPED: 0.5,
}
_CACHE_TTL = timedelta(hours=settings.AI_PICKS_CACHE_HOURS)


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


class CandidateRecord(BaseModel):
    game_id: int
    name: str
    genres: list[str]
    tags: list[str]
    platforms: list[str]
    release_year: int | None = None
    hltb_main_hours: float | None = None
    rating: float | None = None
    metacritic: int | None = None


class AIPick(BaseModel):
    game_id: int
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    because_you_liked: list[str] = Field(default_factory=list)


class AIPicksSelection(BaseModel):
    taste_summary: str
    picks: list[AIPick]


def _redis_client():
    return redis_lib.from_url(settings.REDIS_URL)


def _dossier_cache_key(user_id: int) -> str:
    return f"ai_picks:dossier:{user_id}"


def _dirty_cache_key(user_id: int) -> str:
    return f"ai_picks:dirty:{user_id}"


def _truncate(text: str | None, limit: int = 120) -> str:
    if not text:
        return ""
    trimmed = " ".join(text.split())
    if len(trimmed) <= limit:
        return trimmed
    return trimmed[: limit - 1].rstrip() + "…"


def _entry_weight(entry: LibraryEntry) -> float:
    if entry.rating is not None:
        return float(entry.rating)
    return _STATUS_WEIGHTS.get(entry.status, 2.0)


def _era_label(year: int | None) -> str | None:
    if not year:
        return None
    return f"{(year // 10) * 10}s"


def _length_bucket(hours: float | None) -> str:
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
    try:
        r = _redis_client()
        ttl_seconds = max(int(_CACHE_TTL.total_seconds()), 60)
        r.delete(_dossier_cache_key(user_id))
        r.setex(_dirty_cache_key(user_id), ttl_seconds, "1")
    except Exception:
        pass


def _clear_dirty_flag(user_id: int) -> None:
    try:
        _redis_client().delete(_dirty_cache_key(user_id))
    except Exception:
        pass


def _is_dirty(user_id: int) -> bool:
    try:
        return bool(_redis_client().get(_dirty_cache_key(user_id)))
    except Exception:
        return False


def _load_cached_dossier(user_id: int) -> TasteDossier | None:
    try:
        payload = _redis_client().get(_dossier_cache_key(user_id))
        if not payload:
            return None
        return TasteDossier.model_validate(json.loads(payload))
    except Exception:
        return None


def _store_cached_dossier(user_id: int, dossier: TasteDossier) -> None:
    try:
        _redis_client().setex(
            _dossier_cache_key(user_id),
            int(_CACHE_TTL.total_seconds()),
            json.dumps(dossier.model_dump()),
        )
    except Exception:
        pass


def build_compact_taste_summary(user_id: int, db: Session) -> CompactTasteSummary:
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

        for genre in (game.genres or []):
            genre_weights[genre["name"]] += max(weight, 0.5)
        for tag in (game.tags or []):
            tag_name = tag.get("name")
            if not tag_name or tag.get("language", "eng") not in ("eng", ""):
                continue
            if entry.status == LibraryStatus.DROPPED or (entry.rating is not None and entry.rating <= 2.5):
                avoid_tag_weights[tag_name] += 1.5
            elif weight >= 3.0:
                tag_weights[tag_name] += weight
        for platform in (game.platforms or []):
            platform_name = platform.get("name")
            if platform_name:
                platform_weights[platform_name] += max(weight, 0.5)

        era = _era_label(release_year)
        if era and weight >= 3.0:
            era_weights[era] += weight
        if weight >= 3.0 and length_hours is not None:
            length_votes.append(_length_bucket(length_hours))

        if entry.rating is not None and entry.rating >= 4:
            positive_games.append((entry.rating, game.name))
        elif entry.status == LibraryStatus.COMPLETED:
            positive_games.append((weight, game.name))

        if entry.status == LibraryStatus.DROPPED:
            negative_games.append((5.0, game.name))
        elif entry.rating is not None and entry.rating <= 2.5:
            negative_games.append((5.0 - entry.rating, game.name))

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


def _score_candidate(game: Game, dossier: TasteDossier) -> float:
    genre_names = {genre.get("name", "").lower() for genre in (game.genres or []) if genre.get("name")}
    tag_names = {
        tag.get("name", "").lower()
        for tag in (game.tags or [])
        if tag.get("name") and tag.get("language", "eng") in ("eng", "")
    }
    platform_names = {platform.get("name", "").lower() for platform in (game.platforms or []) if platform.get("name")}

    preferred_genres = {name.lower() for name in dossier.preferred_genres}
    preferred_tags = {name.lower() for name in dossier.preferred_tags}
    preferred_platforms = {name.lower() for name in dossier.preferred_platforms}
    avoid_tags = {name.lower() for name in dossier.avoid_tags}

    genre_overlap = len(genre_names & preferred_genres)
    tag_overlap = len(tag_names & preferred_tags)
    platform_overlap = len(platform_names & preferred_platforms)
    total_overlap = genre_overlap + tag_overlap + platform_overlap
    if total_overlap == 0:
        return 0.0

    score = 0.0
    score += genre_overlap * 3.0
    score += tag_overlap * 2.0
    score += platform_overlap * 1.25
    score -= len(tag_names & avoid_tags) * 2.5
    score += (game.rating or 0.0) / 5.0
    score += (game.metacritic or 0) / 100.0
    score += min(game.ratings_count or 0, 5000) / 5000.0

    release_year = game.released.year if game.released else None
    if _era_label(release_year) and _era_label(release_year) in dossier.preferred_eras:
        score += 0.75

    game_hours = game.hltb_main_hours or (float(game.playtime) if game.playtime else None)
    if _length_bucket(game_hours) == dossier.length_preference:
        score += 0.5

    return score


def build_candidate_shortlist(user_id: int, dossier: TasteDossier, db: Session) -> list[CandidateRecord]:
    owned_game_ids = {
        entry.game_id
        for entry in db.query(LibraryEntry).filter(LibraryEntry.user_id == user_id).all()
    }

    query = db.query(Game).filter(Game.genres.isnot(None))
    if owned_game_ids:
        query = query.filter(~Game.id.in_(owned_game_ids))

    candidates: list[tuple[float, Game]] = []
    for game in query.all():
        score = _score_candidate(game, dossier)
        if score <= 0:
            continue
        candidates.append((score, game))

    candidates.sort(key=lambda item: item[0], reverse=True)
    shortlist = []
    for _, game in candidates[: settings.AI_PICKS_MAX_CANDIDATES]:
        shortlist.append(
            CandidateRecord(
                game_id=game.id,
                name=game.name,
                genres=[genre.get("name", "") for genre in (game.genres or [])[:4] if genre.get("name")],
                tags=[
                    tag.get("name", "")
                    for tag in (game.tags or [])
                    if tag.get("name") and tag.get("language", "eng") in ("eng", "")
                ][:5],
                platforms=[platform.get("name", "") for platform in (game.platforms or [])[:3] if platform.get("name")],
                release_year=game.released.year if game.released else None,
                hltb_main_hours=game.hltb_main_hours,
                rating=game.rating,
                metacritic=game.metacritic,
            )
        )

    if not shortlist:
        raise ValueError("Not enough catalog candidates match this user's taste yet.")
    return shortlist


def _selection_prompt(dossier: TasteDossier, candidates: list[CandidateRecord]) -> str:
    candidate_lines = [
        (
            f"{candidate.game_id} | {candidate.name} | "
            f"genres={', '.join(candidate.genres) or 'n/a'} | "
            f"tags={', '.join(candidate.tags) or 'n/a'} | "
            f"platforms={', '.join(candidate.platforms) or 'n/a'} | "
            f"year={candidate.release_year or 'n/a'} | "
            f"hltb={candidate.hltb_main_hours or 'n/a'} | "
            f"rating={candidate.rating or 'n/a'} | "
            f"metacritic={candidate.metacritic or 'n/a'}"
        )
        for candidate in candidates
    ]
    return (
        "Choose the strongest final recommendations from this allowed catalog only.\n"
        "Do not invent games, IDs, or unsupported claims. Keep explanations concise and specific.\n\n"
        f"Taste dossier:\n{json.dumps(dossier.model_dump(), ensure_ascii=True)}\n\n"
        "Allowed candidates:\n"
        + "\n".join(candidate_lines)
    )


def _validate_selection(
    selection: AIPicksSelection,
    candidate_ids: set[int],
    owned_game_ids: set[int],
) -> AIPicksSelection:
    if not selection.taste_summary.strip():
        raise ValueError("Missing taste summary from AI Picks response.")
    if not selection.picks:
        raise ValueError("AI Picks returned no recommendations.")
    if len(selection.picks) > settings.AI_PICKS_MAX_RESULTS:
        raise ValueError("AI Picks returned too many recommendations.")

    seen: set[int] = set()
    for pick in selection.picks:
        if pick.game_id not in candidate_ids:
            raise ValueError(f"AI Picks returned unknown game id {pick.game_id}.")
        if pick.game_id in owned_game_ids:
            raise ValueError(f"AI Picks returned owned game id {pick.game_id}.")
        if pick.game_id in seen:
            raise ValueError("AI Picks returned duplicate games.")
        if not pick.explanation.strip():
            raise ValueError("AI Picks returned an empty explanation.")
        seen.add(pick.game_id)

    return selection


def _generate_selection_once(dossier: TasteDossier, candidates: list[CandidateRecord], *, stricter: bool = False) -> AIPicksSelection:
    provider = get_default_llm_provider()
    user_prompt = _selection_prompt(dossier, candidates)
    if stricter:
        user_prompt += (
            "\n\nRepair mode: you must only use candidate IDs from the list, no duplicates, "
            "and no more than the requested number of picks."
        )
    return provider.generate_structured(
        system_prompt=(
            "You are an expert game curator. Choose only from the provided candidates and return valid JSON."
        ),
        user_prompt=user_prompt,
        schema=AIPicksSelection,
    )


def generate_ai_picks_for_recommendation(recommendation_id: int, user_id: int, db: Session) -> Recommendation:
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
    candidates = build_candidate_shortlist(user_id, dossier, db)
    owned_game_ids = {
        entry.game_id
        for entry in db.query(LibraryEntry).filter(LibraryEntry.user_id == user_id).all()
    }
    candidate_ids = {candidate.game_id for candidate in candidates}

    try:
        selection = _generate_selection_once(dossier, candidates, stricter=False)
        selection = _validate_selection(selection, candidate_ids, owned_game_ids)
    except (ValueError, LLMProviderError):
        selection = _generate_selection_once(dossier, candidates, stricter=True)
        selection = _validate_selection(selection, candidate_ids, owned_game_ids)

    recommendation.items.clear()
    recommendation.profile_snapshot = {
        "compact_summary": compact_summary.model_dump(),
        "taste_dossier": dossier.model_dump(),
    }
    recommendation.summary = selection.taste_summary
    recommendation.model_name = settings.AI_PICKS_MODEL
    recommendation.status = RecommendationStatus.READY
    recommendation.generated_at = datetime.now(timezone.utc)

    for rank, pick in enumerate(selection.picks, start=1):
        recommendation.items.append(
            RecommendationItem(
                game_id=pick.game_id,
                rank=rank,
                score=float(pick.confidence),
                explanation=pick.explanation.strip(),
                confidence=float(pick.confidence),
                because_you_liked=pick.because_you_liked or None,
            )
        )

    db.commit()
    db.refresh(recommendation)
    _clear_dirty_flag(user_id)
    return recommendation


def _latest_ai_picks_query(user_id: int, db: Session):
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
    if not settings.GEMINI_API_KEY:
        raise ValueError("AI Picks is not configured yet. Add GEMINI_API_KEY to enable it.")

    build_compact_taste_summary(user_id, db)

    latest = _latest_ai_picks_query(user_id, db).first()
    if latest is not None:
        if latest.status == RecommendationStatus.PENDING:
            return latest, False
        if latest.status == RecommendationStatus.READY and not _is_stale(latest, user_id):
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
