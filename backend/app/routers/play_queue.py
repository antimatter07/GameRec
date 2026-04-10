from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.play_queue import PlayQueueEnqueue, PlayQueueOut, PlayQueueReorder
from app.services import play_queue_service

router = APIRouter()

DBDep          = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(require_basic)]


@router.get("/", response_model=PlayQueueOut)
def get_queue(db: DBDep, current_user: CurrentUserDep):
    return play_queue_service.get_queue(db, current_user.id)


@router.post("/", response_model=PlayQueueOut, status_code=status.HTTP_201_CREATED)
def enqueue_game(payload: PlayQueueEnqueue, db: DBDep, current_user: CurrentUserDep):
    return play_queue_service.enqueue(db, current_user.id, payload)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def dequeue_game(entry_id: int, db: DBDep, current_user: CurrentUserDep):
    play_queue_service.dequeue(db, current_user.id, entry_id)


@router.put("/order", response_model=PlayQueueOut)
def reorder_queue(payload: PlayQueueReorder, db: DBDep, current_user: CurrentUserDep):
    return play_queue_service.reorder(db, current_user.id, payload)
