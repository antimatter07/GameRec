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
    PaginatedPlaythroughNotesOut,
    PaginatedSessionsOut,
    PlaythroughNoteCreate,
    PlaythroughNoteOut,
    PlaythroughNoteUpdate,
    SessionLogCreate,
    SessionLogOut,
    SessionLogUpdate,
)
from app.services import journal_service
from app.services.ai_picks_service import invalidate_ai_picks_cache

router = APIRouter()

DBDep          = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User,    Depends(require_basic)]


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionLogOut, status_code=status.HTTP_201_CREATED)
def log_session(payload: SessionLogCreate, db: DBDep, current_user: CurrentUserDep):
    """Log session.

    Creates a journal session log for the current user.

    Args:
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    result = journal_service.create_session(db, current_user.id, payload)
    invalidate_ai_picks_cache(current_user.id)
    return result


# NOTE: /sessions/stats must be before /sessions/{session_id} to avoid path-param clash.
@router.get("/sessions/stats", response_model=JournalStats)
def get_stats(db: DBDep, current_user: CurrentUserDep):
    """Get stats.

    Returns aggregate statistics for the current route domain.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.get_stats(db, current_user.id)


@router.get("/sessions", response_model=PaginatedSessionsOut)
def list_sessions(
    db: DBDep,
    current_user: CurrentUserDep,
    game_id:  int | None = Query(None),
    page:     int        = Query(1, ge=1),
    per_page: int        = Query(20, ge=1, le=100),
):
    """List sessions.

    Returns paginated journal sessions for the current user.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.
        game_id: ID of the game to read or update. Defaults to Query(None).
        page: One-based page number to return. Defaults to 1.
        per_page: per page value used by the operation. Defaults to Query(20, ge=1, le=100).

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.list_sessions(db, current_user.id, game_id, page, per_page)


@router.patch("/sessions/{session_id}", response_model=SessionLogOut)
def update_session(
    session_id: int,
    payload: SessionLogUpdate,
    db: DBDep,
    current_user: CurrentUserDep,
):
    """Update session.

    Updates a journal session owned by the current user.

    Args:
        session_id: ID of the journal session being read or modified.
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    result = journal_service.update_session(db, current_user.id, session_id, payload)
    invalidate_ai_picks_cache(current_user.id)
    return result


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: DBDep, current_user: CurrentUserDep):
    """Delete session.

    Deletes a journal session owned by the current user.

    Args:
        session_id: ID of the journal session being read or modified.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        None."""
    journal_service.delete_session(db, current_user.id, session_id)
    invalidate_ai_picks_cache(current_user.id)


@router.get("/feed", response_model=PaginatedSessionsOut)
def get_feed(
    db: DBDep,
    current_user: CurrentUserDep,
    page:     int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Get feed.

    Returns the combined journal activity feed for the current user.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.
        page: One-based page number to return. Defaults to 1.
        per_page: per page value used by the operation. Defaults to Query(20, ge=1, le=100).

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.get_feed(db, current_user.id, page, per_page)


# ─── Scratchpad Notes ─────────────────────────────────────────────────────────

@router.post("/notes", response_model=PlaythroughNoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: PlaythroughNoteCreate, db: DBDep, current_user: CurrentUserDep):
    """Create note.

    Creates a playthrough note for the current user.

    Args:
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.create_note(db, current_user.id, payload)


@router.get("/notes", response_model=PaginatedPlaythroughNotesOut)
def list_notes(
    db: DBDep,
    current_user: CurrentUserDep,
    game_id: int | None = Query(None),
    status_value: str | None = Query(None, alias="status"),
    kind: str | None = Query(None),
    pinned: bool | None = Query(None),
    remind_next_session: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """List notes.

    Returns filtered playthrough notes for the current user.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.
        game_id: ID of the game to read or update. Defaults to Query(None).
        status_value: Optional note status filter. Defaults to Query(None, alias='status').
        kind: Optional note kind filter. Defaults to Query(None).
        pinned: pinned value used by the operation. Defaults to Query(None).
        remind_next_session: remind next session value used by the operation. Defaults to Query(None).
        page: One-based page number to return. Defaults to 1.
        per_page: per page value used by the operation. Defaults to Query(50, ge=1, le=100).

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.list_notes(
        db,
        current_user.id,
        game_id,
        status_value,
        kind,
        pinned,
        remind_next_session,
        page,
        per_page,
    )


@router.patch("/notes/{note_id}", response_model=PlaythroughNoteOut)
def update_note(
    note_id: int,
    payload: PlaythroughNoteUpdate,
    db: DBDep,
    current_user: CurrentUserDep,
):
    """Update note.

    Updates a playthrough note owned by the current user.

    Args:
        note_id: ID of the playthrough note being read or modified.
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.update_note(db, current_user.id, note_id, payload)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: DBDep, current_user: CurrentUserDep):
    """Delete note.

    Deletes a playthrough note owned by the current user.

    Args:
        note_id: ID of the playthrough note being read or modified.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        None."""
    journal_service.delete_note(db, current_user.id, note_id)


# ─── Multi-Axis Ratings ───────────────────────────────────────────────────────

@router.put("/ratings/{game_id}", response_model=MultiAxisRatingOut)
def upsert_rating(
    game_id: int,
    payload: MultiAxisRatingUpsert,
    db: DBDep,
    current_user: CurrentUserDep,
):
    """Create or update rating.

    Creates or updates a multi-axis game rating for the current user.

    Args:
        game_id: ID of the game to read or update.
        payload: Validated request payload or event payload for the operation.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    result = journal_service.upsert_rating(db, current_user.id, game_id, payload)
    invalidate_ai_picks_cache(current_user.id)
    return result


@router.get("/ratings", response_model=list[MultiAxisRatingOut])
def get_all_ratings(db: DBDep, current_user: CurrentUserDep):
    """Get all ratings.

    Returns all multi-axis game ratings for the current user.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.get_all_ratings(db, current_user.id)


# NOTE: /ratings must be before /ratings/{game_id} to avoid matching "ratings" as a game_id.
@router.get("/ratings/{game_id}", response_model=MultiAxisRatingOut)
def get_rating(game_id: int, db: DBDep, current_user: CurrentUserDep):
    """Get rating.

    Returns the current user rating for one game.

    Args:
        game_id: ID of the game to read or update.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
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
    """Get emotion stats.

    Returns emotion trends and aggregate journal sentiment for the current user.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.
        period: period value used by the operation. Defaults to Query('30d', pattern='^(7d|30d|90d|all)$').
        game_id: ID of the game to read or update. Defaults to Query(None).
        genre: Optional genre filter reserved for recommendation queries. Defaults to Query(None).

    Returns:
        Serialized response object or task result produced by the operation."""
    return journal_service.get_emotion_stats(db, current_user.id, period, game_id, genre)
