from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import Text, case, cast, func
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.journal import GameRating
from app.models.library import LibraryEntry, LibraryStatus
from app.schemas.library import LibraryEntryCreate, LibraryEntryUpdate

QUEUEABLE_LIBRARY_STATUSES = {LibraryStatus.BACKLOG, LibraryStatus.REPLAYING}
LIBRARY_QUERY_STATUS = Literal["all", "playing", "replaying", "completed", "backlog", "wishlist", "dropped"]
LIBRARY_QUERY_SORT = Literal["added_at_desc", "added_at_asc", "status"]
STATUS_SORT_ORDER: dict[LibraryStatus, int] = {
    LibraryStatus.PLAYING: 0,
    LibraryStatus.REPLAYING: 1,
    LibraryStatus.BACKLOG: 2,
    LibraryStatus.WISHLIST: 3,
    LibraryStatus.COMPLETED: 4,
    LibraryStatus.DROPPED: 5,
}


def _sync_overall_rating(db: Session, user_id: int, game_id: int, rating_value: float | None) -> None:
    rating = (
        db.query(GameRating)
        .filter(GameRating.user_id == user_id, GameRating.game_id == game_id)
        .first()
    )
    if rating:
        rating.overall = rating_value
    elif rating_value is not None:
        db.add(GameRating(user_id=user_id, game_id=game_id, overall=rating_value))


def _direct_similarity(entry: LibraryEntry, taste_profile: list[float] | None) -> float | None:
    if not taste_profile or not entry.game or not entry.game.feature_vector:
        return None
    dot = sum(float(a) * float(b) for a, b in zip(entry.game.feature_vector, taste_profile))
    return max(0.0, min(1.0, dot))


def _library_query(
    db: Session,
    user_id: int,
    status_filter: LIBRARY_QUERY_STATUS = "all",
    search: str | None = None,
):
    query = (
        db.query(LibraryEntry)
        .join(LibraryEntry.game)
        .filter(LibraryEntry.user_id == user_id)
    )

    if status_filter != "all":
        query = query.filter(LibraryEntry.status == LibraryStatus(status_filter))

    normalized_search = search.strip() if search else None
    if normalized_search:
        query = query.filter(Game.name.ilike(f"%{normalized_search}%"))

    return query


def _order_library_query(query, sort: LIBRARY_QUERY_SORT = "added_at_desc"):
    if sort == "added_at_asc":
        return query.order_by(LibraryEntry.added_at.asc())
    elif sort == "status":
        return query.order_by(
            case(
                *[(LibraryEntry.status == status, order) for status, order in STATUS_SORT_ORDER.items()],
                else_=len(STATUS_SORT_ORDER),
            ),
            LibraryEntry.added_at.desc(),
        )

    return query.order_by(LibraryEntry.added_at.desc())


def get_user_library(
    db: Session,
    user_id: int,
    status_filter: LIBRARY_QUERY_STATUS = "all",
    search: str | None = None,
    sort: LIBRARY_QUERY_SORT = "added_at_desc",
) -> list[LibraryEntry]:
    query = _library_query(db, user_id, status_filter, search).options(joinedload(LibraryEntry.game))
    query = _order_library_query(query, sort)

    return query.all()


def get_user_library_page(
    db: Session,
    user_id: int,
    status_filter: LIBRARY_QUERY_STATUS = "all",
    search: str | None = None,
    sort: LIBRARY_QUERY_SORT = "added_at_desc",
    page: int = 1,
    page_size: int = 40,
) -> dict:
    base_query = _library_query(db, user_id, status_filter, search)
    total = base_query.count()
    entries = (
        _order_library_query(base_query.options(joinedload(LibraryEntry.game)), sort)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"total": total, "page": page, "page_size": page_size, "results": entries}


def add_game(db: Session, user_id: int, entry_in: LibraryEntryCreate) -> LibraryEntry:
    game = db.query(Game).filter(Game.id == entry_in.game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    existing = (
        db.query(LibraryEntry)
        .filter(LibraryEntry.user_id == user_id, LibraryEntry.game_id == entry_in.game_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game already in library")

    entry = LibraryEntry(user_id=user_id, **entry_in.model_dump())
    db.add(entry)
    if entry_in.rating is not None:
        _sync_overall_rating(db, user_id, entry_in.game_id, entry_in.rating)
    db.commit()
    db.refresh(entry)
    # Re-fetch with game relationship loaded for the response
    return db.query(LibraryEntry).filter(LibraryEntry.id == entry.id).options(joinedload(LibraryEntry.game)).first()


def update_entry(db: Session, user_id: int, entry_id: int, updates: LibraryEntryUpdate) -> dict:
    entry = (
        db.query(LibraryEntry)
        .filter(LibraryEntry.id == entry_id, LibraryEntry.user_id == user_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")

    changed_fields = updates.model_dump(exclude_unset=True)
    for field, value in changed_fields.items():
        setattr(entry, field, value)
    if "rating" in changed_fields:
        _sync_overall_rating(db, user_id, entry.game_id, updates.rating)

    queue_result = {"queue_removed": False, "next_game_candidate": None}
    if updates.status is not None and updates.status not in QUEUEABLE_LIBRARY_STATUSES:
        from app.services.play_queue_service import remove_entry_from_queue
        queue_result = remove_entry_from_queue(db, user_id, entry_id)

    db.commit()
    db.refresh(entry)

    updated_entry = (
        db.query(LibraryEntry).filter(LibraryEntry.id == entry.id).options(joinedload(LibraryEntry.game)).first()
    )

    return {
        "entry": updated_entry,
        "queue_removed": queue_result["queue_removed"],
        "next_game_candidate": queue_result["next_game_candidate"],
        "queue_advanced": False,
        "next_game": None,
    }


def get_stats(db: Session, user_id: int) -> dict:
    entries = get_user_library(db, user_id)

    by_status: dict[str, int] = {s.value: 0 for s in LibraryStatus}
    ratings: list[float] = []
    genre_counts: dict[str, int] = defaultdict(int)

    for entry in entries:
        by_status[entry.status.value] += 1
        if entry.rating is not None:
            ratings.append(entry.rating)
        for genre in (entry.game.genres or []):
            genre_counts[genre["name"]] += 1

    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    top_genres = sorted(
        [{"genre": name, "count": count} for name, count in genre_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:5]

    return {
        "total_games": len(entries),
        "by_status": by_status,
        "avg_rating": avg_rating,
        "top_genres": top_genres,
    }


def get_prioritized_backlog(
    db: Session,
    user_id: int,
    mood_genre: str | None = None,
    max_hours: int | None = None,
    sort: Literal["score", "playtime_asc", "playtime_desc", "added_at"] = "score",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Return the user's BACKLOG entries ranked by a composite priority score:
        0.5 * taste_score  (cosine similarity from latest recommendation batch)
      + 0.3 * staleness    (how long since the entry was last touched)
      + 0.2 * playtime     (shorter games surface higher)
    """
    query = (
        db.query(LibraryEntry)
        .filter(LibraryEntry.user_id == user_id, LibraryEntry.status == LibraryStatus.BACKLOG)
        .join(LibraryEntry.game)
        .options(joinedload(LibraryEntry.game))
    )

    if mood_genre:
        query = query.filter(cast(Game.genres, Text).ilike(f'%"name": "{mood_genre}"%'))

    if max_hours is not None:
        query = query.filter(
            func.coalesce(Game.hltb_main_hours, Game.playtime) <= max_hours
        )

    entries = query.all()

    taste_profile: list[float] | None = None
    try:
        from app.services.recommendation_service import build_user_taste_profile

        taste_profile = build_user_taste_profile(user_id, db).tolist()
    except ValueError:
        taste_profile = None

    now = datetime.now(timezone.utc)

    def _stale_months(updated_at: datetime) -> int:
        dt = updated_at if updated_at.tzinfo else updated_at.replace(tzinfo=timezone.utc)
        return int((now - dt).days / 30)

    def _playtime_hours(game: Game) -> float | None:
        if game.hltb_main_hours is not None:
            return game.hltb_main_hours
        if game.playtime is not None:
            return float(game.playtime)
        return None

    def _priority(entry: LibraryEntry) -> float:
        taste = _direct_similarity(entry, taste_profile) or 0.5
        stale = min(1.0, _stale_months(entry.updated_at) / 6)
        hours = _playtime_hours(entry.game)
        playtime = (1 - min(1.0, hours / 100)) if hours is not None else 0.5
        return 0.5 * taste + 0.3 * stale + 0.2 * playtime

    results = [
        {
            "entry_id":      e.id,
            "game":          e.game,
            "playtime_hours": _playtime_hours(e.game),
            "taste_score":   _direct_similarity(e, taste_profile),
            "priority_score": _priority(e),
            "stale_months":  _stale_months(e.updated_at),
            "_added_at":     e.added_at,  # used for sort only, not in response
        }
        for e in entries
    ]

    sort_key = {
        "score":        lambda x: -x["priority_score"],
        "playtime_asc": lambda x: (x["playtime_hours"] is None, x["playtime_hours"] or 0),
        "playtime_desc": lambda x: (x["playtime_hours"] is None, -(x["playtime_hours"] or 0)),
        "added_at":     lambda x: x["_added_at"],
    }
    results.sort(key=sort_key[sort])

    # Strip internal sort key before returning
    for r in results:
        del r["_added_at"]

    total = len(results)
    offset = (page - 1) * page_size
    return {"total": total, "results": results[offset: offset + page_size]}


def remove_game(db: Session, user_id: int, entry_id: int) -> None:
    entry = db.query(LibraryEntry).filter(LibraryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    if entry.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your library entry")
    db.delete(entry)
    db.commit()
