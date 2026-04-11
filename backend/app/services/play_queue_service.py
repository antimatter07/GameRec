from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from app.models.library import LibraryEntry, LibraryStatus
from app.models.play_queue import PlayQueueEntry
from app.schemas.play_queue import PlayQueueEnqueue, PlayQueueReorder


def _load_queue(db: Session, user_id: int) -> list[PlayQueueEntry]:
    return (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id)
        .order_by(PlayQueueEntry.position)
        .options(
            joinedload(PlayQueueEntry.entry).joinedload(LibraryEntry.game)
        )
        .all()
    )


def _to_out(rows: list[PlayQueueEntry]) -> dict:
    return {"total": len(rows), "entries": rows}


def get_queue(db: Session, user_id: int) -> dict:
    return _to_out(_load_queue(db, user_id))


def enqueue(db: Session, user_id: int, payload: PlayQueueEnqueue) -> dict:
    entry = (
        db.query(LibraryEntry)
        .filter(LibraryEntry.id == payload.entry_id, LibraryEntry.user_id == user_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    if entry.status != LibraryStatus.BACKLOG:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only backlog games can be added to the queue",
        )

    existing = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id, PlayQueueEntry.entry_id == payload.entry_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This game is already in your queue")

    max_pos = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id)
        .count()
    )
    queue_entry = PlayQueueEntry(user_id=user_id, entry_id=payload.entry_id, position=max_pos + 1)
    db.add(queue_entry)
    db.commit()

    return _to_out(_load_queue(db, user_id))


def dequeue(db: Session, user_id: int, entry_id: int) -> None:
    queue_entry = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id, PlayQueueEntry.entry_id == entry_id)
        .first()
    )
    if not queue_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not in queue")

    removed_pos = queue_entry.position
    db.delete(queue_entry)
    db.flush()

    # Compact positions for all entries after the removed one
    db.execute(
        update(PlayQueueEntry)
        .where(PlayQueueEntry.user_id == user_id, PlayQueueEntry.position > removed_pos)
        .values(position=PlayQueueEntry.position - 1)
    )
    db.commit()


def reorder(db: Session, user_id: int, payload: PlayQueueReorder) -> dict:
    current = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id)
        .all()
    )
    current_ids = {row.entry_id for row in current}
    requested_ids = set(payload.ordered_entry_ids)

    if current_ids != requested_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The provided list does not match your current queue",
        )

    entry_map = {row.entry_id: row for row in current}
    n = len(current)

    # Shift all positions out of range first to avoid unique constraint conflicts
    # during the intermediate state when two rows would temporarily share a position.
    for row in current:
        row.position += n
    db.flush()

    for new_pos, entry_id in enumerate(payload.ordered_entry_ids, start=1):
        entry_map[entry_id].position = new_pos
    db.commit()

    return _to_out(_load_queue(db, user_id))


def advance_queue_after_completion(db: Session, user_id: int, completed_entry_id: int) -> dict:
    """
    Called after a library entry is marked 'completed'.
    If the entry was in the queue:
      - Remove it from the queue
      - Mark the new position-1 entry as 'playing'
    Returns metadata for the API response.
    """
    queue_entry = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id, PlayQueueEntry.entry_id == completed_entry_id)
        .first()
    )
    if not queue_entry:
        return {"queue_advanced": False, "next_game": None}

    removed_pos = queue_entry.position
    db.delete(queue_entry)
    db.flush()

    # Compact positions
    db.execute(
        update(PlayQueueEntry)
        .where(PlayQueueEntry.user_id == user_id, PlayQueueEntry.position > removed_pos)
        .values(position=PlayQueueEntry.position - 1)
    )
    db.flush()

    # Find new head
    next_queue_entry = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id, PlayQueueEntry.position == 1)
        .options(joinedload(PlayQueueEntry.entry).joinedload(LibraryEntry.game))
        .first()
    )
    if not next_queue_entry:
        db.commit()
        return {"queue_advanced": False, "next_game": None}

    next_library_entry = next_queue_entry.entry
    next_library_entry.status = LibraryStatus.PLAYING
    db.commit()
    db.refresh(next_library_entry)

    return {"queue_advanced": True, "next_game": next_library_entry}
