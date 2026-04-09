from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import Text, cast, func
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.library import LibraryEntry, LibraryStatus
from app.models.recommendation import Recommendation, RecommendationItem
from app.schemas.library import LibraryEntryCreate, LibraryEntryUpdate


def get_user_library(db: Session, user_id: int) -> list[LibraryEntry]:
    return (
        db.query(LibraryEntry)
        .filter(LibraryEntry.user_id == user_id)
        .options(joinedload(LibraryEntry.game))
        .all()
    )


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
    db.commit()
    db.refresh(entry)
    # Re-fetch with game relationship loaded for the response
    return db.query(LibraryEntry).filter(LibraryEntry.id == entry.id).options(joinedload(LibraryEntry.game)).first()


def update_entry(db: Session, user_id: int, entry_id: int, updates: LibraryEntryUpdate) -> LibraryEntry:
    entry = (
        db.query(LibraryEntry)
        .filter(LibraryEntry.id == entry_id, LibraryEntry.user_id == user_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return db.query(LibraryEntry).filter(LibraryEntry.id == entry.id).options(joinedload(LibraryEntry.game)).first()


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

    # Load taste scores from the user's latest recommendation batch.
    latest_rec = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user_id)
        .order_by(Recommendation.generated_at.desc())
        .first()
    )
    taste_scores: dict[int, float] = {}
    if latest_rec:
        items = (
            db.query(RecommendationItem)
            .filter(RecommendationItem.recommendation_id == latest_rec.id)
            .all()
        )
        taste_scores = {item.game_id: item.score for item in items}

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
        taste = taste_scores.get(entry.game_id, 0.5)
        stale = min(1.0, _stale_months(entry.updated_at) / 6)
        hours = _playtime_hours(entry.game)
        playtime = (1 - min(1.0, hours / 100)) if hours is not None else 0.5
        return 0.5 * taste + 0.3 * stale + 0.2 * playtime

    results = [
        {
            "entry_id":      e.id,
            "game":          e.game,
            "playtime_hours": _playtime_hours(e.game),
            "taste_score":   taste_scores.get(e.game_id),
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
