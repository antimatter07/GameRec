from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.journal import GameRating, PlaythroughNote, SessionLog
from app.models.library import LibraryEntry, LibraryStatus
from app.schemas.journal import (
    DailyHoursItem,
    EmotionFrequencyItem,
    EmotionGameCorrelation,
    EmotionGenreCorrelation,
    EmotionMonthlyBucket,
    EmotionStats,
    JournalStats,
    MultiAxisRatingOut,
    MultiAxisRatingUpsert,
    PaginatedPlaythroughNotesOut,
    PlaythroughNoteCreate,
    PlaythroughNoteOut,
    PlaythroughNoteUpdate,
    SessionLogCreate,
    SessionLogOut,
    SessionLogUpdate,
    TopGenreItem,
)

_POSITIVE_EMOTIONS = {'happy', 'proud', 'relaxed'}
_NEGATIVE_EMOTIONS = {'frustrated', 'angry', 'bored', 'disappointed', 'sad', 'creeped_out'}
_NOTE_KINDS = {"goal", "note", "recipe", "location", "build", "quest"}
_NOTE_STATUSES = {"open", "done", "archived"}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_session(db: Session, session_id: int, user_id: int) -> SessionLog:
    """Load session.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        session_id: ID of the play session to load or modify.
        user_id: ID of the user whose data should be read or modified.

    Returns:
        SessionLog produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return session


def _session_to_out(s: SessionLog) -> SessionLogOut:
    """Session to out.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        s: Session log model to serialize.

    Returns:
        SessionLogOut produced by the operation."""
    game = s.game
    return SessionLogOut(
        id=s.id,
        user_id=s.user_id,
        game_id=s.game_id,
        library_entry_id=s.library_entry_id,
        started_at=s.started_at,
        ended_at=s.ended_at,
        duration_minutes=s.duration_minutes,
        notes=s.notes,
        is_milestone=s.is_milestone,
        milestone_label=s.milestone_label,
        emotions=s.emotions,
        created_at=s.created_at,
        game_title=game.name if game else None,
        game_cover_url=game.background_image if game else None,
        game_genres=[g["name"] for g in (game.genres or [])] if game else [],
    )


def _note_to_out(note: PlaythroughNote) -> PlaythroughNoteOut:
    """Note to out.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        note: note value used by the operation.

    Returns:
        PlaythroughNoteOut produced by the operation."""
    game = note.game
    return PlaythroughNoteOut(
        id=note.id,
        user_id=note.user_id,
        game_id=note.game_id,
        library_entry_id=note.library_entry_id,
        session_log_id=note.session_log_id,
        kind=note.kind,
        title=note.title,
        body=note.body,
        status=note.status,
        pinned=note.pinned,
        remind_next_session=note.remind_next_session,
        completed_at=note.completed_at,
        created_at=note.created_at,
        updated_at=note.updated_at,
        game_title=game.name if game else None,
        game_cover_url=game.background_image if game else None,
    )


def _fetch_with_game(db: Session, session_id: int) -> SessionLog:
    """Fetch with game.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        session_id: ID of the play session to load or modify.

    Returns:
        SessionLog produced by the operation."""
    return (
        db.query(SessionLog)
        .filter(SessionLog.id == session_id)
        .options(joinedload(SessionLog.game))
        .first()
    )


def _fetch_note_with_game(db: Session, note_id: int) -> PlaythroughNote | None:
    """Fetch note with game.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        note_id: ID of the playthrough note to load or modify.

    Returns:
        PlaythroughNote | None when a matching value is available; otherwise None."""
    return (
        db.query(PlaythroughNote)
        .filter(PlaythroughNote.id == note_id)
        .options(joinedload(PlaythroughNote.game))
        .first()
    )


def _rating_to_out(r: GameRating, game: Game | None) -> MultiAxisRatingOut:
    """Rating to out.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        r: Rating model to serialize.
        game: Game model or normalized game dictionary to inspect.

    Returns:
        MultiAxisRatingOut produced by the operation."""
    return MultiAxisRatingOut(
        id=r.id,
        user_id=r.user_id,
        game_id=r.game_id,
        library_entry_id=r.library_entry_id,
        story=r.story,
        gameplay=r.gameplay,
        visuals=r.visuals,
        soundtrack=r.soundtrack,
        overall=r.overall,
        created_at=r.created_at,
        updated_at=r.updated_at,
        game_title=game.name if game else None,
        game_cover_url=game.background_image if game else None,
    )


def _validate_note_kind(kind: str) -> str:
    """Validate note kind.

    Normalizes and checks incoming values before they are used in database writes or AI workflows.

    Args:
        kind: Raw note kind value to validate.

    Returns:
        String value produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    if kind not in _NOTE_KINDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid note kind: {kind}",
        )
    return kind


def _validate_note_status(status_value: str) -> str:
    """Validate note status.

    Normalizes and checks incoming values before they are used in database writes or AI workflows.

    Args:
        status_value: Raw status value to validate.

    Returns:
        String value produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    if status_value not in _NOTE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid note status: {status_value}",
        )
    return status_value


def _resolve_library_entry(
    db: Session,
    *,
    user_id: int,
    game_id: int,
    library_entry_id: int | None,
) -> LibraryEntry | None:
    """Resolve library entry.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        game_id: ID of the game to read, update, or associate with the operation.
        library_entry_id: library entry id value used by the operation.

    Returns:
        LibraryEntry | None when a matching value is available; otherwise None.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    if library_entry_id is None:
        return None
    linked_entry = (
        db.query(LibraryEntry)
        .filter(
            LibraryEntry.id == library_entry_id,
            LibraryEntry.user_id == user_id,
            LibraryEntry.game_id == game_id,
        )
        .first()
    )
    if linked_entry is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Library entry does not belong to this user and game",
        )
    return linked_entry


def _create_follow_up_note(
    db: Session,
    *,
    user_id: int,
    game_id: int,
    library_entry_id: int | None,
    session_log_id: int,
    title: str | None,
) -> PlaythroughNote | None:
    """Create follow up note.

    Validates the input, persists the relevant model changes, and returns the updated service representation.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        game_id: ID of the game to read, update, or associate with the operation.
        library_entry_id: library entry id value used by the operation.
        session_log_id: session log id value used by the operation.
        title: Game title to normalize or inspect.

    Returns:
        PlaythroughNote | None when a matching value is available; otherwise None."""
    if not title:
        return None

    trimmed = title.strip()
    if not trimmed:
        return None

    note = PlaythroughNote(
        user_id=user_id,
        game_id=game_id,
        library_entry_id=library_entry_id,
        session_log_id=session_log_id,
        kind="goal",
        title=trimmed,
        status="open",
        pinned=True,
        remind_next_session=True,
    )
    db.add(note)
    return note


# ─── Session CRUD ─────────────────────────────────────────────────────────────

def create_session(db: Session, user_id: int, payload: SessionLogCreate) -> SessionLogOut:
    """Create session.

    Validates the input, persists the relevant model changes, and returns the updated service representation.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        payload: Validated input payload for the operation.

    Returns:
        SessionLogOut produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    game = db.query(Game).filter(Game.id == payload.game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    linked_entry = _resolve_library_entry(
        db,
        user_id=user_id,
        game_id=payload.game_id,
        library_entry_id=payload.library_entry_id,
    )

    data = payload.model_dump(exclude={"follow_up_note_title"})
    data["started_at"] = datetime.now(timezone.utc)
    # Validate emotions: keep only non-empty list, otherwise store None
    if data.get("emotions") is not None and len(data["emotions"]) == 0:
        data["emotions"] = None

    entry = SessionLog(user_id=user_id, **data)
    db.add(entry)
    db.flush()

    _create_follow_up_note(
        db,
        user_id=user_id,
        game_id=payload.game_id,
        library_entry_id=payload.library_entry_id,
        session_log_id=entry.id,
        title=payload.follow_up_note_title,
    )

    db.commit()
    db.refresh(entry)

    lib_entry = linked_entry or (
        db.query(LibraryEntry)
        .filter(LibraryEntry.user_id == user_id, LibraryEntry.game_id == payload.game_id)
        .first()
    )
    if lib_entry:
        if lib_entry.status in (LibraryStatus.BACKLOG, LibraryStatus.WISHLIST):
            lib_entry.status = LibraryStatus.PLAYING
            db.commit()
        elif lib_entry.status == LibraryStatus.COMPLETED:
            lib_entry.status = LibraryStatus.REPLAYING
            db.commit()

    loaded = _fetch_with_game(db, entry.id)
    return _session_to_out(loaded)


def list_sessions(
    db: Session,
    user_id: int,
    game_id: int | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """List sessions.

    Builds the database query, applies caller-provided filters, and returns the requested slice of results.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        game_id: ID of the game to read, update, or associate with the operation. Defaults to None.
        page: One-based page number to return. Defaults to 1.
        per_page: Maximum number of records to return per page. Defaults to 20.

    Returns:
        Dictionary containing serialized service state and metadata."""
    query = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id)
        .options(joinedload(SessionLog.game))
        .order_by(SessionLog.started_at.desc())
    )
    if game_id is not None:
        query = query.filter(SessionLog.game_id == game_id)

    total = query.count()
    results = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [_session_to_out(s) for s in results],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
    }


# ─── Scratchpad CRUD ──────────────────────────────────────────────────────────

def create_note(db: Session, user_id: int, payload: PlaythroughNoteCreate) -> PlaythroughNoteOut:
    """Create note.

    Validates the input, persists the relevant model changes, and returns the updated service representation.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        payload: Validated input payload for the operation.

    Returns:
        PlaythroughNoteOut produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    game = db.query(Game).filter(Game.id == payload.game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    linked_entry = _resolve_library_entry(
        db,
        user_id=user_id,
        game_id=payload.game_id,
        library_entry_id=payload.library_entry_id,
    )
    kind = _validate_note_kind(payload.kind)
    note_status = _validate_note_status(payload.status)
    title = payload.title.strip()
    body = payload.body.strip() if payload.body else None

    note = PlaythroughNote(
        user_id=user_id,
        game_id=payload.game_id,
        library_entry_id=linked_entry.id if linked_entry else None,
        session_log_id=payload.session_log_id,
        kind=kind,
        title=title,
        body=body or None,
        status=note_status,
        pinned=payload.pinned,
        remind_next_session=payload.remind_next_session,
        completed_at=datetime.now(timezone.utc) if note_status == "done" else None,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    loaded = _fetch_note_with_game(db, note.id)
    if not loaded:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Note could not be loaded")
    return _note_to_out(loaded)


def list_notes(
    db: Session,
    user_id: int,
    game_id: int | None = None,
    status_value: str | None = None,
    kind: str | None = None,
    pinned: bool | None = None,
    remind_next_session: bool | None = None,
    page: int = 1,
    per_page: int = 50,
) -> PaginatedPlaythroughNotesOut:
    """List notes.

    Builds the database query, applies caller-provided filters, and returns the requested slice of results.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        game_id: ID of the game to read, update, or associate with the operation. Defaults to None.
        status_value: Raw status value to validate. Defaults to None.
        kind: Raw note kind value to validate. Defaults to None.
        pinned: pinned value used by the operation. Defaults to None.
        remind_next_session: remind next session value used by the operation. Defaults to None.
        page: One-based page number to return. Defaults to 1.
        per_page: Maximum number of records to return per page. Defaults to 50.

    Returns:
        PaginatedPlaythroughNotesOut produced by the operation."""
    if status_value is not None:
        _validate_note_status(status_value)
    if kind is not None:
        _validate_note_kind(kind)

    query = (
        db.query(PlaythroughNote)
        .filter(PlaythroughNote.user_id == user_id)
        .options(joinedload(PlaythroughNote.game))
        .order_by(
            PlaythroughNote.pinned.desc(),
            PlaythroughNote.remind_next_session.desc(),
            PlaythroughNote.updated_at.desc(),
        )
    )
    if game_id is not None:
        query = query.filter(PlaythroughNote.game_id == game_id)
    if status_value is not None:
        query = query.filter(PlaythroughNote.status == status_value)
    if kind is not None:
        query = query.filter(PlaythroughNote.kind == kind)
    if pinned is not None:
        query = query.filter(PlaythroughNote.pinned == pinned)
    if remind_next_session is not None:
        query = query.filter(PlaythroughNote.remind_next_session == remind_next_session)

    total = query.count()
    results = query.offset((page - 1) * per_page).limit(per_page).all()
    return PaginatedPlaythroughNotesOut(
        items=[_note_to_out(note) for note in results],
        total=total,
        page=page,
        per_page=per_page,
        has_next=(page * per_page) < total,
    )


def update_note(
    db: Session,
    user_id: int,
    note_id: int,
    payload: PlaythroughNoteUpdate,
) -> PlaythroughNoteOut:
    """Update note.

    Applies validated field changes to an existing record and commits the updated state.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        note_id: ID of the playthrough note to load or modify.
        payload: Validated input payload for the operation.

    Returns:
        PlaythroughNoteOut produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    note = db.query(PlaythroughNote).filter(PlaythroughNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your note")

    updates = payload.model_dump(exclude_unset=True)
    if "kind" in updates and updates["kind"] is not None:
        updates["kind"] = _validate_note_kind(updates["kind"])
    if "status" in updates and updates["status"] is not None:
        updates["status"] = _validate_note_status(updates["status"])
    if "title" in updates and updates["title"] is not None:
        updates["title"] = updates["title"].strip()
    if "body" in updates:
        updates["body"] = updates["body"].strip() if updates["body"] else None

    for field, value in updates.items():
        setattr(note, field, value)

    if "status" in updates:
        if updates["status"] == "done":
            note.completed_at = note.completed_at or datetime.now(timezone.utc)
        else:
            note.completed_at = None

    db.commit()
    loaded = _fetch_note_with_game(db, note.id)
    if not loaded:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Note could not be loaded")
    return _note_to_out(loaded)


def delete_note(db: Session, user_id: int, note_id: int) -> None:
    """Delete note.

    Verifies ownership or existence, removes the target record, and commits the change.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        note_id: ID of the playthrough note to load or modify.

    Returns:
        None.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    note = db.query(PlaythroughNote).filter(PlaythroughNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your note")
    db.delete(note)
    db.commit()


def update_session(
    db: Session, user_id: int, session_id: int, payload: SessionLogUpdate
) -> SessionLogOut:
    """Update session.

    Applies validated field changes to an existing record and commits the updated state.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        session_id: ID of the play session to load or modify.
        payload: Validated input payload for the operation.

    Returns:
        SessionLogOut produced by the operation."""
    session = _load_session(db, session_id, user_id)
    updates = payload.model_dump(exclude_unset=True)
    # Normalise empty emotions list to None
    if "emotions" in updates and updates["emotions"] is not None and len(updates["emotions"]) == 0:
        updates["emotions"] = None
    for field, value in updates.items():
        setattr(session, field, value)
    db.commit()
    loaded = _fetch_with_game(db, session.id)
    return _session_to_out(loaded)


def delete_session(db: Session, user_id: int, session_id: int) -> None:
    """Delete session.

    Verifies ownership or existence, removes the target record, and commits the change.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        session_id: ID of the play session to load or modify.

    Returns:
        None."""
    session = _load_session(db, session_id, user_id)
    db.delete(session)
    db.commit()


def get_feed(db: Session, user_id: int, page: int = 1, per_page: int = 20) -> dict:
    """Get feed.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        page: One-based page number to return. Defaults to 1.
        per_page: Maximum number of records to return per page. Defaults to 20.

    Returns:
        Dictionary containing serialized service state and metadata."""
    query = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id)
        .options(joinedload(SessionLog.game))
        .order_by(SessionLog.started_at.desc())
    )
    total = query.count()
    results = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [_session_to_out(s) for s in results],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
    }


# ─── Stats ────────────────────────────────────────────────────────────────────

def get_stats(db: Session, user_id: int) -> JournalStats:
    """Get stats.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.

    Returns:
        JournalStats produced by the operation."""
    all_sessions = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id)
        .options(joinedload(SessionLog.game))
        .all()
    )

    now = datetime.now(timezone.utc)
    today = now.date()

    current_month = now.month
    current_year  = now.year

    if current_month == 1:
        prev_month, prev_year = 12, current_year - 1
    else:
        prev_month, prev_year = current_month - 1, current_year

    week_start = today - timedelta(days=6)
    prev_week_start = week_start - timedelta(days=7)

    total_minutes_all_time   = 0
    total_minutes_this_month = 0
    total_minutes_this_week  = 0
    prev_week_minutes        = 0
    sessions_this_month      = 0
    sessions_prev_month      = 0
    games_this_month: set[int] = set()
    genre_minutes: dict[str, float] = defaultdict(float)
    session_dates: list[date] = []
    daily_minutes: dict[str, float] = defaultdict(float)

    # Emotion tracking for this month
    emotion_counts_month: dict[str, int] = defaultdict(int)
    sessions_with_emotions_this_month = 0

    for s in all_sessions:
        minutes = s.duration_minutes or 0
        started = s.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        s_date = started.date()
        session_dates.append(s_date)
        total_minutes_all_time += minutes

        if started.month == current_month and started.year == current_year:
            total_minutes_this_month += minutes
            sessions_this_month += 1
            games_this_month.add(s.game_id)
            for genre in (s.game.genres or []):
                genre_minutes[genre["name"]] += minutes / 60
            # Emotion aggregation for this month
            if s.emotions:
                sessions_with_emotions_this_month += 1
                for e in s.emotions:
                    emotion_counts_month[e] += 1

        if started.month == prev_month and started.year == prev_year:
            sessions_prev_month += 1

        if week_start <= s_date <= today:
            total_minutes_this_week += minutes
            day_label = s_date.strftime("%a")
            daily_minutes[day_label] += minutes

        if prev_week_start <= s_date < week_start:
            prev_week_minutes += minutes

    current_streak, longest_streak = _compute_streaks(session_dates)

    top_genres = sorted(
        [TopGenreItem(genre=name, hours=round(hours, 1)) for name, hours in genre_minutes.items()],
        key=lambda x: x.hours,
        reverse=True,
    )[:5]

    last_7: list[DailyHoursItem] = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        label = d.strftime("%a")
        last_7.append(DailyHoursItem(day=label, hours=round(daily_minutes.get(label, 0.0), 1)))

    def pct_change(current: float, previous: float) -> float:
        """Pct change.

        Performs the service operation behind a stable module-level interface.

        Args:
            current: current value used by the operation.
            previous: previous value used by the operation.

        Returns:
            Floating-point value produced by the operation."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    hours_change_pct_week      = pct_change(total_minutes_this_week / 60, prev_week_minutes / 60)
    sessions_change_pct_month  = pct_change(sessions_this_month, sessions_prev_month)

    library_entries = (
        db.query(LibraryEntry)
        .filter(LibraryEntry.user_id == user_id)
        .all()
    )
    games_completed  = sum(1 for e in library_entries if e.status == LibraryStatus.COMPLETED)
    games_in_backlog = sum(1 for e in library_entries if e.status == LibraryStatus.BACKLOG)
    games_playing    = sum(1 for e in library_entries if e.status in (LibraryStatus.PLAYING, LibraryStatus.REPLAYING))

    # Emotion summary fields
    dominant_emotion_this_month: str | None = None
    emotion_coverage_pct:        float | None = None

    if sessions_this_month > 0:
        emotion_coverage_pct = round(
            (sessions_with_emotions_this_month / sessions_this_month) * 100, 1
        )
    if emotion_counts_month:
        dominant_emotion_this_month = max(emotion_counts_month, key=emotion_counts_month.get)

    return JournalStats(
        total_hours_all_time=round(total_minutes_all_time / 60, 1),
        total_hours_this_month=round(total_minutes_this_month / 60, 1),
        total_hours_this_week=round(total_minutes_this_week / 60, 1),
        sessions_this_month=sessions_this_month,
        games_played_this_month=len(games_this_month),
        top_genres_this_month=top_genres,
        current_streak_days=current_streak,
        longest_streak_days=longest_streak,
        daily_hours_this_week=last_7,
        hours_change_pct_week=hours_change_pct_week,
        sessions_change_pct_month=sessions_change_pct_month,
        games_completed=games_completed,
        games_in_backlog=games_in_backlog,
        games_playing=games_playing,
        dominant_emotion_this_month=dominant_emotion_this_month,
        emotion_coverage_pct=emotion_coverage_pct,
    )


# ─── Ratings CRUD ─────────────────────────────────────────────────────────────

def upsert_rating(
    db: Session, user_id: int, game_id: int, payload: MultiAxisRatingUpsert
) -> MultiAxisRatingOut:
    """Create or update rating.

    Validates the input, persists the relevant model changes, and returns the updated service representation.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        game_id: ID of the game to read, update, or associate with the operation.
        payload: Validated input payload for the operation.

    Returns:
        MultiAxisRatingOut produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    rating = (
        db.query(GameRating)
        .filter(GameRating.user_id == user_id, GameRating.game_id == game_id)
        .first()
    )

    if rating:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rating, field, value)
    else:
        rating = GameRating(user_id=user_id, game_id=game_id, **payload.model_dump())
        db.add(rating)

    if "overall" in payload.model_dump(exclude_unset=True):
        lib_entry = (
            db.query(LibraryEntry)
            .filter(LibraryEntry.user_id == user_id, LibraryEntry.game_id == game_id)
            .first()
        )
        if lib_entry:
            lib_entry.rating = payload.overall

    db.commit()
    db.refresh(rating)
    return _rating_to_out(rating, game)


def get_rating(db: Session, user_id: int, game_id: int) -> MultiAxisRatingOut:
    """Get rating.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        game_id: ID of the game to read, update, or associate with the operation.

    Returns:
        MultiAxisRatingOut produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    rating = (
        db.query(GameRating)
        .filter(GameRating.user_id == user_id, GameRating.game_id == game_id)
        .options(joinedload(GameRating.game))
        .first()
    )
    if not rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return _rating_to_out(rating, rating.game)


def get_all_ratings(db: Session, user_id: int) -> list[MultiAxisRatingOut]:
    """Get all ratings.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.

    Returns:
        List of matching records or serialized service objects."""
    ratings = (
        db.query(GameRating)
        .filter(GameRating.user_id == user_id)
        .options(joinedload(GameRating.game))
        .all()
    )
    return [_rating_to_out(r, r.game) for r in ratings]


# ─── Emotion Stats ────────────────────────────────────────────────────────────

def get_emotion_stats(
    db: Session,
    user_id: int,
    period: str = "30d",
    game_id: int | None = None,
    genre: str | None = None,
) -> EmotionStats:
    """Get emotion stats.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        period: period value used by the operation. Defaults to '30d'.
        game_id: ID of the game to read, update, or associate with the operation. Defaults to None.
        genre: Optional genre slug or name used to filter games. Defaults to None.

    Returns:
        EmotionStats produced by the operation."""
    now = datetime.now(timezone.utc)
    if period == "7d":
        start = now - timedelta(days=7)
    elif period == "30d":
        start = now - timedelta(days=30)
    elif period == "90d":
        start = now - timedelta(days=90)
    else:
        start = None

    query = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id)
        .options(joinedload(SessionLog.game))
    )
    if start:
        query = query.filter(SessionLog.started_at >= start)
    if game_id is not None:
        query = query.filter(SessionLog.game_id == game_id)

    all_sessions = query.all()

    # Filter by genre at Python level (genres stored as JSON)
    if genre:
        all_sessions = [
            s for s in all_sessions
            if s.game and any(
                g["name"].lower() == genre.lower()
                for g in (s.game.genres or [])
            )
        ]

    total_sessions = len(all_sessions)
    sessions_with_emotions = [s for s in all_sessions if s.emotions]
    total_with_emotions = len(sessions_with_emotions)

    # ── Overall frequency ─────────────────────────────────────────────────────
    emotion_counts: dict[str, int] = defaultdict(int)
    for s in sessions_with_emotions:
        for e in s.emotions:
            emotion_counts[e] += 1

    frequency = [
        EmotionFrequencyItem(
            emotion=e,
            session_count=cnt,
            percentage=round((cnt / total_with_emotions) * 100, 1) if total_with_emotions > 0 else 0.0,
        )
        for e, cnt in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    most_common = frequency[0].emotion if frequency else None

    # ── Per-game correlations ─────────────────────────────────────────────────
    game_emotion_map: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    game_session_count: dict[int, int] = defaultdict(int)
    game_info: dict[int, Game] = {}

    for s in sessions_with_emotions:
        game_emotion_map[s.game_id]
        for e in s.emotions:
            game_emotion_map[s.game_id][e] += 1
        game_session_count[s.game_id] += 1
        if s.game:
            game_info[s.game_id] = s.game

    per_game: list[EmotionGameCorrelation] = []
    for gid, counts in game_emotion_map.items():
        if not counts:
            continue
        dominant = max(counts, key=counts.get)
        g = game_info.get(gid)
        per_game.append(EmotionGameCorrelation(
            game_id=gid,
            game_title=g.name if g else f"Game #{gid}",
            cover_url=g.background_image if g else None,
            dominant_emotion=dominant,
            session_count=game_session_count[gid],
        ))
    per_game.sort(key=lambda x: x.session_count, reverse=True)

    positive_games = [g for g in per_game if g.dominant_emotion in _POSITIVE_EMOTIONS]
    negative_games = [g for g in per_game if g.dominant_emotion in _NEGATIVE_EMOTIONS]
    top_positive_game = positive_games[0] if positive_games else None
    top_negative_game = negative_games[0] if negative_games else None

    # ── Per-genre correlations ────────────────────────────────────────────────
    genre_emotion_map: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    genre_session_count: dict[str, int] = defaultdict(int)

    for s in sessions_with_emotions:
        game_genres = [g["name"] for g in (s.game.genres or [])] if s.game else []
        for g_name in game_genres:
            for e in s.emotions:
                genre_emotion_map[g_name][e] += 1
            genre_session_count[g_name] += 1

    per_genre: list[EmotionGenreCorrelation] = []
    for g_name, counts in genre_emotion_map.items():
        if not counts:
            continue
        dominant = max(counts, key=counts.get)
        total_g = sum(counts.values())
        breakdown = [
            EmotionFrequencyItem(
                emotion=e,
                session_count=cnt,
                percentage=round((cnt / total_g) * 100, 1) if total_g > 0 else 0.0,
            )
            for e, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
        per_genre.append(EmotionGenreCorrelation(
            genre=g_name,
            dominant_emotion=dominant,
            session_count=genre_session_count[g_name],
            emotion_breakdown=breakdown,
        ))
    per_genre.sort(key=lambda x: x.session_count, reverse=True)

    # ── Monthly breakdown (last 6 months) ────────────────────────────────────
    monthly_data: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for s in sessions_with_emotions:
        started = s.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        month_key = started.strftime("%Y-%m")
        for e in s.emotions:
            monthly_data[month_key][e] += 1

    monthly_breakdown: list[EmotionMonthlyBucket] = []
    for month_key in sorted(monthly_data.keys(), reverse=True)[:6]:
        counts = monthly_data[month_key]
        total_m = sum(counts.values())
        freq = [
            EmotionFrequencyItem(
                emotion=e,
                session_count=cnt,
                percentage=round((cnt / total_m) * 100, 1) if total_m > 0 else 0.0,
            )
            for e, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
        monthly_breakdown.append(EmotionMonthlyBucket(month=month_key, frequency=freq))

    return EmotionStats(
        period=period,
        total_sessions_with_emotions=total_with_emotions,
        total_sessions=total_sessions,
        frequency=frequency,
        most_common_emotion=most_common,
        top_positive_game=top_positive_game,
        top_negative_game=top_negative_game,
        per_game=per_game[:10],
        per_genre=per_genre[:10],
        monthly_breakdown=monthly_breakdown,
    )


# ─── Streak helpers ───────────────────────────────────────────────────────────

def _compute_streaks(session_dates: list[date]) -> tuple[int, int]:
    """Compute streaks.

    Aggregates source data for recommendation and AI workflows.

    Args:
        session_dates: session dates value used by the operation.

    Returns:
        Tuple containing the primary result and related status metadata."""
    if not session_dates:
        return 0, 0

    unique_asc = sorted(set(session_dates))
    today = date.today()

    unique_desc = list(reversed(unique_asc))
    current = 0
    prev: date | None = None
    for d in unique_desc:
        if prev is None:
            if (today - d).days > 1:
                break
            current = 1
            prev = d
        else:
            if (prev - d).days == 1:
                current += 1
                prev = d
            else:
                break

    if len(unique_asc) == 0:
        return current, 0
    longest = 1
    run = 1
    for i in range(1, len(unique_asc)):
        if (unique_asc[i] - unique_asc[i - 1]).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    return current, longest
