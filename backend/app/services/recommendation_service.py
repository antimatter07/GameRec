from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy.orm import Session, joinedload

from app.models.library import LibraryEntry, LibraryStatus
from app.models.game import Game
from app.models.recommendation import Recommendation, RecommendationItem, RecommendationKind, RecommendationStatus
from app.models.user import User

# Weight assigned to a library entry based on its status when no explicit
# rating is present.
_STATUS_WEIGHTS: dict[LibraryStatus, float] = {
    LibraryStatus.COMPLETED: 4.0,
    LibraryStatus.PLAYING:   3.0,
    LibraryStatus.BACKLOG:   2.0,
    LibraryStatus.DROPPED:   1.0,
}

_DEFAULT_WEIGHT = 2.0
_CACHE_TTL = 3600  # seconds
_RECOMMENDATION_TTL = timedelta(hours=1)
_TOP_N = 20


def build_user_taste_profile(user_id: int, db: Session) -> np.ndarray:
    """
    Aggregate the user's rated/tracked library entries into a taste-profile
    vector.

    1. Load all LibraryEntry rows for the user, eagerly loading game.feature_vector.
    2. Filter out entries whose game has no feature_vector.
    3. Assign a weight per entry:
       - If a numeric rating (1–5) is present: weight = rating
       - Otherwise: weight derived from status (see _STATUS_WEIGHTS)
    4. Compute a weighted average of the game feature vectors.
    5. L2-normalise the result.
    6. Attempt to cache the serialised vector in Redis (key "taste:{user_id}",
       TTL 3600 s).  Redis errors are silently swallowed so the service keeps
       working when Redis is unavailable.
    7. Return the profile as a 1-D numpy float32 array.

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
            weight = float(entry.rating)
        else:
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
        from app.config import settings
        import redis as redis_lib

        r = redis_lib.from_url(settings.REDIS_URL)
        r.setex(f"taste:{user_id}", _CACHE_TTL, profile_f32.tobytes())
    except Exception:
        pass  # Redis unavailable — proceed without caching

    return profile_f32


def compute_recommendations(user_id: int, db: Session) -> Recommendation:
    """
    Content-based filtering via cosine similarity.

    1. Build the user's taste profile vector.
    2. Load all Game rows that have a feature_vector.
    3. Exclude games already present in the user's library.
    4. Compute dot-product similarity (both vectors are L2-normalised, so
       this equals cosine similarity).
    5. Sort descending and take the top _TOP_N results.
    6. Persist a Recommendation + RecommendationItem rows and return.
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
    candidates = [g for g in candidate_games if g.rawg_id not in library_rawg_ids]

    if not candidates:
        raise ValueError(
            f"No candidate games available for user {user_id} "
            "(all vectorised games are already in the user's library)."
        )

    # Compute cosine similarities via vectorised dot product
    matrix = np.array([g.feature_vector for g in candidates], dtype=np.float32)
    scores: np.ndarray = matrix.dot(taste_vec)  # shape (N,)

    # Sort descending and take top _TOP_N
    top_indices = np.argsort(scores)[::-1][:_TOP_N]

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
            score=float(scores[int(idx)]),
        )
        db.add(item)

    db.commit()
    db.refresh(recommendation)
    return recommendation


def get_or_generate(user_id: int, db: Session) -> Recommendation:
    """Return a recent cached recommendation or generate a fresh one.

    If a Recommendation for this user was generated within the last hour it is
    returned as-is.  Otherwise a new one is computed and returned.
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
