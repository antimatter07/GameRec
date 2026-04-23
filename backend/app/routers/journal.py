from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.journal import (
    EmotionStats,
    JournalStats,
    MultiAxisRatingOut,
    MultiAxisRatingUpsert,
    PaginatedSessionsOut,
    SessionLogCreate,
    SessionLogOut,
    SessionLogUpdate,
)
from app.services import journal_service

router = APIRouter()

DBDep          = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User,    Depends(require_basic)]


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionLogOut, status_code=status.HTTP_201_CREATED)
def log_session(payload: SessionLogCreate, db: DBDep, current_user: CurrentUserDep):
    return journal_service.create_session(db, current_user.id, payload)


# NOTE: /sessions/stats must be before /sessions/{session_id} to avoid path-param clash.
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


# ─── Multi-Axis Ratings ───────────────────────────────────────────────────────

@router.put("/ratings/{game_id}", response_model=MultiAxisRatingOut)
def upsert_rating(
    game_id: int,
    payload: MultiAxisRatingUpsert,
    db: DBDep,
    current_user: CurrentUserDep,
):
    return journal_service.upsert_rating(db, current_user.id, game_id, payload)


@router.get("/ratings", response_model=list[MultiAxisRatingOut])
def get_all_ratings(db: DBDep, current_user: CurrentUserDep):
    return journal_service.get_all_ratings(db, current_user.id)


# NOTE: /ratings must be before /ratings/{game_id} to avoid matching "ratings" as a game_id.
@router.get("/ratings/{game_id}", response_model=MultiAxisRatingOut)
def get_rating(game_id: int, db: DBDep, current_user: CurrentUserDep):
    return journal_service.get_rating(db, current_user.id, game_id)


# ─── Emotion Stats ────────────────────────────────────────────────────────────

@router.get("/emotions/stats", response_model=EmotionStats)
def get_emotion_stats(
    db: DBDep,
    current_user: CurrentUserDep,
    period:  str      = Query("30d", pattern="^(7d|30d|90d|all)$"),
    game_id: int | None = Query(None),
    genre:   str | None = Query(None),
):
    return journal_service.get_emotion_stats(db, current_user.id, period, game_id, genre)
