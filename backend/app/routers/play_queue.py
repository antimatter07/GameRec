from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic, require_queue_suggestions
from app.models.user import User
from app.schemas.play_queue import (
    PlayQueueEnqueue,
    PlayQueueOut,
    PlayQueueReorder,
    QueueSuggestionEnsureIn,
    QueueSuggestionStateOut,
)
from app.services import play_queue_service
from app.services import task_queue
from app.services.queue_suggestion_service import adopt_queue_suggestion, ensure_queue_suggestion, get_queue_suggestion_state

router = APIRouter()

DBDep          = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(require_basic)]


@router.get("", response_model=PlayQueueOut)
def get_queue(db: DBDep, current_user: CurrentUserDep):
    """Get queue.

    Returns the current user play queue.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return play_queue_service.get_queue(db, current_user.id)


@router.post("", response_model=PlayQueueOut, status_code=status.HTTP_201_CREATED)
def enqueue_game(payload: PlayQueueEnqueue, db: DBDep, current_user: CurrentUserDep):
    """Enqueue game.

    Adds a library entry to the current user play queue.

    Args:
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return play_queue_service.enqueue(db, current_user.id, payload)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def dequeue_game(entry_id: int, db: DBDep, current_user: CurrentUserDep):
    """Dequeue game.

    Removes one entry from the current user play queue.

    Args:
        entry_id: ID of the library or queue entry being modified.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    play_queue_service.dequeue(db, current_user.id, entry_id)


@router.put("/order", response_model=PlayQueueOut)
def reorder_queue(payload: PlayQueueReorder, db: DBDep, current_user: CurrentUserDep):
    """Reorder queue.

    Persists a new play queue order for the current user.

    Args:
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return play_queue_service.reorder(db, current_user.id, payload)


@router.get("/suggestion", response_model=QueueSuggestionStateOut)
def get_queue_suggestion(
    db: DBDep,
    current_user: Annotated[User, Depends(require_queue_suggestions)],
):
    """Get queue suggestion.

    Returns the current AI queue suggestion state.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return get_queue_suggestion_state(current_user.id, db)


@router.post("/suggestion/ensure", response_model=QueueSuggestionStateOut)
def ensure_queue_suggestion_for_user(
    payload: QueueSuggestionEnsureIn,
    db: DBDep,
    current_user: Annotated[User, Depends(require_queue_suggestions)],
):
    """Ensure queue suggestion for user.

    Ensures a queue suggestion exists and dispatches generation when needed.

    Args:
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    state, should_enqueue, suggestion_id = ensure_queue_suggestion(current_user.id, payload.trigger_source, db)
    if should_enqueue and suggestion_id is not None:
        try:
            task_queue.enqueue_queue_suggestion(suggestion_id, current_user.id)
        except Exception:
            pass
    return state


@router.post("/suggestion/adopt", response_model=PlayQueueOut)
def adopt_queue_suggestion_for_user(
    db: DBDep,
    current_user: Annotated[User, Depends(require_queue_suggestions)],
):
    """Adopt queue suggestion for user.

    Applies the latest AI queue suggestion to the current user queue.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        HTTPException: When the request cannot be authorized, validated, or completed."""
    try:
        return adopt_queue_suggestion(current_user.id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
