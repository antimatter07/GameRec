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
    """Return the authenticated user's current play queue."""
    return play_queue_service.get_queue(db, current_user.id)


@router.post("", response_model=PlayQueueOut, status_code=status.HTTP_201_CREATED)
def enqueue_game(payload: PlayQueueEnqueue, db: DBDep, current_user: CurrentUserDep):
    """Add a library entry to the play queue."""
    return play_queue_service.enqueue(db, current_user.id, payload)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def dequeue_game(entry_id: int, db: DBDep, current_user: CurrentUserDep):
    """Remove a queue entry from the user's play queue."""
    play_queue_service.dequeue(db, current_user.id, entry_id)


@router.put("/order", response_model=PlayQueueOut)
def reorder_queue(payload: PlayQueueReorder, db: DBDep, current_user: CurrentUserDep):
    """Persist a manual queue reorder supplied by the client."""
    return play_queue_service.reorder(db, current_user.id, payload)


@router.get("/suggestion", response_model=QueueSuggestionStateOut)
def get_queue_suggestion(
    db: DBDep,
    current_user: Annotated[User, Depends(require_queue_suggestions)],
):
    """Return the latest AI suggested play order state for the queue."""
    return get_queue_suggestion_state(current_user.id, db)


@router.post("/suggestion/ensure", response_model=QueueSuggestionStateOut)
def ensure_queue_suggestion_for_user(
    payload: QueueSuggestionEnsureIn,
    db: DBDep,
    current_user: Annotated[User, Depends(require_queue_suggestions)],
):
    """Create or reuse a pending AI play-order suggestion for the queue."""
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
    """Apply the ready AI suggested play order to the queue."""
    try:
        return adopt_queue_suggestion(current_user.id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
