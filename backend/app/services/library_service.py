from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.library import LibraryEntry, LibraryStatus
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


def remove_game(db: Session, user_id: int, entry_id: int) -> None:
    entry = db.query(LibraryEntry).filter(LibraryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    if entry.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your library entry")
    db.delete(entry)
    db.commit()
