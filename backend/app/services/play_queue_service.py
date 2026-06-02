from fastapi import HTTPException, status
from sqlalchemy import func, text, update
from sqlalchemy.orm import Session, joinedload

from app.models.library import LibraryEntry, LibraryStatus
from app.models.play_queue import PlayQueueEntry
from app.schemas.play_queue import PlayQueueEnqueue, PlayQueueReorder

QUEUEABLE_STATUSES = {LibraryStatus.BACKLOG, LibraryStatus.REPLAYING}


def _load_queue(db: Session, user_id: int) -> list[PlayQueueEntry]:
    """Load queue.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.

    Returns:
        List of matching records or serialized service objects."""
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
    """Serialize out.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        rows: rows value used by the operation.

    Returns:
        Dictionary containing serialized service state and metadata."""
    return {"total": len(rows), "entries": rows}


def get_queue(db: Session, user_id: int) -> dict:
    """Get queue.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.

    Returns:
        Dictionary containing serialized service state and metadata."""
    return _to_out(_load_queue(db, user_id))


def enqueue(db: Session, user_id: int, payload: PlayQueueEnqueue) -> dict:
    """Enqueue.

    Performs the service operation behind a stable module-level interface.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        payload: Validated input payload for the operation.

    Returns:
        Dictionary containing serialized service state and metadata.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
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
    """Remove.

    Verifies ownership or existence, removes the target record, and commits the change.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        entry_id: ID of the library or queue entry being modified.

    Returns:
        None.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
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
    """Remove entry from queue.

    Verifies ownership or existence, removes the target record, and commits the change.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        entry_id: ID of the library or queue entry being modified.

    Returns:
        Dictionary containing serialized service state and metadata."""
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
    """Reorder.

    Performs the service operation behind a stable module-level interface.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        payload: Validated input payload for the operation.

    Returns:
        Dictionary containing serialized service state and metadata.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
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
    """Advance queue after completion.

    Performs the service operation behind a stable module-level interface.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        completed_entry_id: completed entry id value used by the operation.

    Returns:
        Dictionary containing serialized service state and metadata."""
    result = remove_entry_from_queue(db, user_id, completed_entry_id)
    db.commit()
    return {
        "queue_advanced": False,
        "next_game": None,
        **result,
    }
