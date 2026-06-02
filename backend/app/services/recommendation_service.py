from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy.orm import Session, joinedload

from app.models.library import LibraryEntry, LibraryStatus
from app.models.game import Game
from app.models.recommendation import Recommendation, RecommendationFeedback, RecommendationItem, RecommendationKind, RecommendationStatus
from app.models.user import User

# Weight assigned to a library entry based on its status when no explicit
# rating is present.
_STATUS_WEIGHTS: dict[LibraryStatus, float] = {
    LibraryStatus.COMPLETED: 4.0,
    LibraryStatus.PLAYING:   3.0,
    LibraryStatus.REPLAYING: 3.0,
    LibraryStatus.BACKLOG:   1.5,
    LibraryStatus.WISHLIST:  0.75,
}

_DEFAULT_WEIGHT = 2.0
_CACHE_TTL = 3600  # seconds
_RECOMMENDATION_TTL = timedelta(hours=1)
_TOP_N = 20


def build_user_taste_profile(user_id: int, db: Session) -> np.ndarray:
    """
    Aggregate the user's library into a normalized taste-profile vector.

    Rated games contribute more strongly than un-rated games, and tracked
    status still provides signal when a rating is absent. The resulting vector
    is used by the cosine-similarity recommender and is cached best-effort in
    Redis for repeat requests.

    Raises ValueError when the user has no library entries that have been
    vectorised yet (i.e., build_vectors.py has not been run, or the user has
    not added any games).
    """
    entries: list[LibraryEntry] = (
        db.query(LibraryEntry)
        .options(joinedload(LibraryEntry.game))
        .filter(LibraryEntry.user_id == user_id)
        .all()
    )

    # Keep only entries where the game already has a feature vector.
    valid = [e for e in entries if e.game and e.game.feature_vector]
    if not valid:
        raise ValueError(
            f"User {user_id} has no library entries with computed feature vectors. "
            "Add games to your library and ensure build_vectors.py has been run."
        )

    dim = len(valid[0].game.feature_vector)
    weighted_sum = np.zeros(dim, dtype=np.float64)
    total_weight = 0.0

    for entry in valid:
        if entry.rating is not None:
            if entry.rating <= 2.5:
                continue
            weight = float(entry.rating)
        else:
            if entry.status == LibraryStatus.DROPPED:
                continue
            weight = _STATUS_WEIGHTS.get(entry.status, _DEFAULT_WEIGHT)

        vec = np.array(entry.game.feature_vector, dtype=np.float64)
        weighted_sum += weight * vec
        total_weight += weight

    if total_weight == 0:
        raise ValueError(f"User {user_id} taste profile has zero total weight.")

    profile = weighted_sum / total_weight

    # L2 normalise
    norm = float(np.linalg.norm(profile))
    if norm > 0:
        profile = profile / norm

    profile_f32 = profile.astype(np.float32)

    # Cache in Redis (best-effort)
    try:
        from app.services import kv_store
        kv_store.set_text(f"taste:{user_id}", profile_f32.tobytes(), ttl_seconds=_CACHE_TTL)
    except Exception:
        pass  # Redis unavailable — proceed without caching

    return profile_f32


def _feedback_adjustments(user_id: int, db: Session) -> tuple[set[int], dict[str, float], dict[str, float]]:
    """Build exact suppressions and lightweight metadata boosts/penalties."""
    feedback_rows = (
        db.query(RecommendationFeedback)
        .join(RecommendationFeedback.item)
        .join(RecommendationItem.recommendation)
        .options(joinedload(RecommendationFeedback.item).joinedload(RecommendationItem.game))
        .filter(Recommendation.user_id == user_id)
        .all()
    )
    suppressed_game_ids: set[int] = set()
    genre_adjustments: dict[str, float] = {}
    tag_adjustments: dict[str, float] = {}

    def bump(target: dict[str, float], name: str | None, delta: float) -> None:
        if name:
            target[name.lower()] = target.get(name.lower(), 0.0) + delta

    for feedback in feedback_rows:
        game = feedback.item.game if feedback.item else None
        if not game:
            continue
        if feedback.is_helpful:
            genre_delta, tag_delta = 0.02, 0.01
        else:
            suppressed_game_ids.add(game.id)
            genre_delta, tag_delta = -0.03, -0.015
        for genre in (game.genres or []):
            bump(genre_adjustments, genre.get("name"), genre_delta)
        for tag in (game.tags or []):
            if tag.get("language", "eng") in ("eng", ""):
                bump(tag_adjustments, tag.get("name"), tag_delta)

    return suppressed_game_ids, genre_adjustments, tag_adjustments


def _apply_feedback_score(game: Game, base_score: float, genre_adjustments: dict[str, float], tag_adjustments: dict[str, float]) -> float:
    score = base_score
    for genre in (game.genres or []):
        score += genre_adjustments.get((genre.get("name") or "").lower(), 0.0)
    for tag in (game.tags or []):
        if tag.get("language", "eng") in ("eng", ""):
            score += tag_adjustments.get((tag.get("name") or "").lower(), 0.0)
    return max(0.0, score)


def compute_recommendations(user_id: int, db: Session) -> Recommendation:
    """
    Generate and persist the core cosine-similarity recommendation batch.

    This is the non-LLM recommendation path for games: it compares the user's
    taste vector to every vectorised game, filters out owned titles, keeps the
    strongest matches, and stores the batch for later display and AI-enhanced
    follow-up tasks.
    """
    taste_vec = build_user_taste_profile(user_id, db)

    # IDs of games the user already owns / has tracked
    library_rawg_ids: set[int] = {
        e.game.rawg_id
        for e in (
            db.query(LibraryEntry)
            .options(joinedload(LibraryEntry.game))
            .filter(LibraryEntry.user_id == user_id)
            .all()
        )
        if e.game
    }

    # Load candidate games
    candidate_games: list[Game] = (
        db.query(Game)
        .filter(Game.feature_vector.isnot(None))
        .all()
    )

    # Filter out library games
    suppressed_game_ids, genre_adjustments, tag_adjustments = _feedback_adjustments(user_id, db)
    candidates = [
        g
        for g in candidate_games
        if g.rawg_id not in library_rawg_ids and g.id not in suppressed_game_ids
    ]

    if not candidates:
        raise ValueError(
            f"No candidate games available for user {user_id} "
            "(all vectorised games are already in the user's library)."
        )

    # Compute cosine similarities via vectorised dot product
    matrix = np.array([g.feature_vector for g in candidates], dtype=np.float32)
    scores: np.ndarray = matrix.dot(taste_vec)  # shape (N,)
    adjusted_scores = np.array(
        [
            _apply_feedback_score(game, float(score), genre_adjustments, tag_adjustments)
            for game, score in zip(candidates, scores)
        ],
        dtype=np.float32,
    )

    # Sort descending and take top _TOP_N
    top_indices = np.argsort(adjusted_scores)[::-1][:_TOP_N]

    # Persist recommendation batch
    recommendation = Recommendation(
        user_id=user_id,
        generated_at=datetime.now(timezone.utc),
        kind=RecommendationKind.COSINE,
        status=RecommendationStatus.READY,
    )
    db.add(recommendation)
    db.flush()  # populate recommendation.id

    for rank, idx in enumerate(top_indices, start=1):
        game = candidates[int(idx)]
        item = RecommendationItem(
            recommendation_id=recommendation.id,
            game_id=game.id,
            rank=rank,
            score=float(adjusted_scores[int(idx)]),
        )
        db.add(item)

    db.commit()
    db.refresh(recommendation)
    return recommendation


def get_or_generate(user_id: int, db: Session) -> Recommendation:
    """Return a cached recommendation batch or generate a fresh one.

    The recommendation feed is cached for a short window so repeated requests
    reuse the same batch unless the cache has aged out.
    """
    cutoff = datetime.now(timezone.utc) - _RECOMMENDATION_TTL

    recent: Recommendation | None = (
        db.query(Recommendation)
        .filter(
            Recommendation.user_id == user_id,
            Recommendation.kind == RecommendationKind.COSINE,
            Recommendation.status == RecommendationStatus.READY,
            Recommendation.generated_at >= cutoff,
        )
        .order_by(Recommendation.generated_at.desc())
        .first()
    )

    if recent is not None:
        return recent

    return compute_recommendations(user_id, db)
