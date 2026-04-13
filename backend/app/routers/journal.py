from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.journal import (
    JournalStats,
    PaginatedSessionsOut,
    SessionLogCreate,
    SessionLogOut,
    SessionLogUpdate,
)
from app.services import journal_service

router = APIRouter()

DBDep          = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User,    Depends(require_basic)]


@router.post("/sessions", response_model=SessionLogOut, status_code=status.HTTP_201_CREATED)
def log_session(payload: SessionLogCreate, db: DBDep, current_user: CurrentUserDep):
    return journal_service.create_session(db, current_user.id, payload)


# NOTE: /sessions/stats must be registered before /sessions/{session_id} so FastAPI
#       matches the literal path "stats" before trying it as a path parameter.
@router.get("/sessions/stats", response_model=JournalStats)
def get_stats(db: DBDep, current_user: CurrentUserDep):
    return journal_service.get_stats(db, current_user.id)


@router.get("/sessions", response_model=PaginatedSessionsOut)
def list_sessions(
    db: DBDep,
    current_user: CurrentUserDep,
    game_id:  int | None = Query(None),
    page:     int        = Query(1, ge=1),
    per_page: int        = Query(20, ge=1, le=100),
):
    return journal_service.list_sessions(db, current_user.id, game_id, page, per_page)


@router.patch("/sessions/{session_id}", response_model=SessionLogOut)
def update_session(
    session_id: int,
    payload: SessionLogUpdate,
    db: DBDep,
    current_user: CurrentUserDep,
):
    return journal_service.update_session(db, current_user.id, session_id, payload)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: DBDep, current_user: CurrentUserDep):
    journal_service.delete_session(db, current_user.id, session_id)


@router.get("/feed", response_model=PaginatedSessionsOut)
def get_feed(
    db: DBDep,
    current_user: CurrentUserDep,
    page:     int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return journal_service.get_feed(db, current_user.id, page, per_page)
