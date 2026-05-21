from fastapi import HTTPException, status
from sqlalchemy import func, text, update
from sqlalchemy.orm import Session, joinedload

from app.models.library import LibraryEntry, LibraryStatus
from app.models.play_queue import PlayQueueEntry
from app.schemas.play_queue import PlayQueueEnqueue, PlayQueueReorder

QUEUEABLE_STATUSES = {LibraryStatus.BACKLOG, LibraryStatus.REPLAYING}


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
    if entry.status not in QUEUEABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only backlog and replaying games can be added to the queue",
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
        .with_entities(func.max(PlayQueueEntry.position))
        .filter(PlayQueueEntry.user_id == user_id)
        .scalar()
    ) or 0
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

    # Defer the position uniqueness check to commit so the bulk decrement does not
    # trigger a per-row constraint violation when PostgreSQL processes rows in an
    # order that temporarily creates a duplicate position mid-statement.
    db.execute(text("SET CONSTRAINTS uq_queue_user_position DEFERRED"))
    db.execute(
        update(PlayQueueEntry)
        .where(PlayQueueEntry.user_id == user_id, PlayQueueEntry.position > removed_pos)
        .values(position=PlayQueueEntry.position - 1)
    )
    db.commit()


def remove_entry_from_queue(db: Session, user_id: int, entry_id: int) -> dict:
    """
    Remove a library entry from the queue, if present, and return the new head as
    a start candidate without mutating that candidate's status.
    """
    queue_entry = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id, PlayQueueEntry.entry_id == entry_id)
        .first()
    )
    if not queue_entry:
        return {"queue_removed": False, "next_game_candidate": None}

    removed_pos = queue_entry.position
    db.delete(queue_entry)
    db.flush()

    db.execute(text("SET CONSTRAINTS uq_queue_user_position DEFERRED"))
    db.execute(
        update(PlayQueueEntry)
        .where(PlayQueueEntry.user_id == user_id, PlayQueueEntry.position > removed_pos)
        .values(position=PlayQueueEntry.position - 1)
    )
    db.flush()

    next_queue_entry = (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id, PlayQueueEntry.position == 1)
        .options(joinedload(PlayQueueEntry.entry).joinedload(LibraryEntry.game))
        .first()
    )
    return {
        "queue_removed": True,
        "next_game_candidate": next_queue_entry.entry if next_queue_entry else None,
    }


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

    # Shift all positions out of range first so no target position collides with
    # an existing position during the per-row ORM updates that follow.
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
      - Promote the new head to 'playing' only if its status is 'backlog'
    Returns metadata for the API response.
    """
    result = remove_entry_from_queue(db, user_id, completed_entry_id)
    db.commit()
    return {
        "queue_advanced": False,
        "next_game": None,
        **result,
    }
