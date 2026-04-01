from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.library import LibraryEntry
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


def remove_game(db: Session, user_id: int, entry_id: int) -> None:
    entry = db.query(LibraryEntry).filter(LibraryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    if entry.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your library entry")
    db.delete(entry)
    db.commit()
