from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.journal import SessionLog
from app.models.library import LibraryEntry, LibraryStatus
from app.schemas.journal import (
    DailyHoursItem,
    JournalStats,
    SessionLogCreate,
    SessionLogOut,
    SessionLogUpdate,
    TopGenreItem,
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_session(db: Session, session_id: int, user_id: int) -> SessionLog:
    """Fetch a session by id, verifying ownership. Raises 404/403 as appropriate."""
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return session


def _session_to_out(s: SessionLog) -> SessionLogOut:
    """Convert a fully-loaded SessionLog ORM object to the flat SessionLogOut schema."""
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
        emotions=None,  # no DB column yet
        created_at=s.created_at,
        game_title=game.name if game else None,
        game_cover_url=game.background_image if game else None,
        game_genres=[g["name"] for g in (game.genres or [])] if game else [],
    )


def _fetch_with_game(db: Session, session_id: int) -> SessionLog:
    """Re-fetch a session with the game relationship eagerly loaded."""
    return (
        db.query(SessionLog)
        .filter(SessionLog.id == session_id)
        .options(joinedload(SessionLog.game))
        .first()
    )


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create_session(db: Session, user_id: int, payload: SessionLogCreate) -> SessionLogOut:
    game = db.query(Game).filter(Game.id == payload.game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    is_first = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id, SessionLog.game_id == payload.game_id)
        .count() == 0
    )

    # emotions are accepted in the payload but not yet persisted (no column)
    data = payload.model_dump(exclude={"emotions"})
    data["started_at"] = datetime.now(timezone.utc)
    entry = SessionLog(user_id=user_id, **data)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    if is_first:
        lib_entry = (
            db.query(LibraryEntry)
            .filter(LibraryEntry.user_id == user_id, LibraryEntry.game_id == payload.game_id)
            .first()
        )
        if lib_entry and lib_entry.status != LibraryStatus.PLAYING:
            lib_entry.status = LibraryStatus.PLAYING
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


def update_session(
    db: Session, user_id: int, session_id: int, payload: SessionLogUpdate
) -> SessionLogOut:
    session = _load_session(db, session_id, user_id)
    # emotions excluded until column exists
    for field, value in payload.model_dump(exclude_unset=True, exclude={"emotions"}).items():
        setattr(session, field, value)
    db.commit()
    loaded = _fetch_with_game(db, session.id)
    return _session_to_out(loaded)


def delete_session(db: Session, user_id: int, session_id: int) -> None:
    session = _load_session(db, session_id, user_id)
    db.delete(session)
    db.commit()


def get_feed(db: Session, user_id: int, page: int = 1, per_page: int = 20) -> dict:
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

    # Previous month bounds for sessions_change_pct
    if current_month == 1:
        prev_month, prev_year = 12, current_year - 1
    else:
        prev_month, prev_year = current_month - 1, current_year

    # Week windows
    week_start = today - timedelta(days=6)   # 7-day window ending today
    prev_week_start = week_start - timedelta(days=7)

    # ── Aggregate sessions ────────────────────────────────────────────────────
    total_minutes_all_time   = 0
    total_minutes_this_month = 0
    total_minutes_this_week  = 0
    prev_week_minutes        = 0
    sessions_this_month      = 0
    sessions_prev_month      = 0
    games_this_month: set[int] = set()
    genre_minutes: dict[str, float] = defaultdict(float)
    session_dates: list[date] = []
    daily_minutes: dict[str, float] = defaultdict(float)  # "Mon" → minutes

    for s in all_sessions:
        minutes = s.duration_minutes or 0
        started = s.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        s_date = started.date()
        session_dates.append(s_date)
        total_minutes_all_time += minutes

        # This month
        if started.month == current_month and started.year == current_year:
            total_minutes_this_month += minutes
            sessions_this_month += 1
            games_this_month.add(s.game_id)
            for genre in (s.game.genres or []):
                genre_minutes[genre["name"]] += minutes / 60

        # Previous month
        if started.month == prev_month and started.year == prev_year:
            sessions_prev_month += 1

        # This week (last 7 days)
        if week_start <= s_date <= today:
            total_minutes_this_week += minutes
            day_label = s_date.strftime("%a")  # "Mon", "Tue", …
            daily_minutes[day_label] += minutes

        # Previous 7-day window
        if prev_week_start <= s_date < week_start:
            prev_week_minutes += minutes

    # ── Streaks ───────────────────────────────────────────────────────────────
    current_streak, longest_streak = _compute_streaks(session_dates)

    # ── Top genres ────────────────────────────────────────────────────────────
    top_genres = sorted(
        [TopGenreItem(genre=name, hours=round(hours, 1)) for name, hours in genre_minutes.items()],
        key=lambda x: x.hours,
        reverse=True,
    )[:5]

    # ── Daily hours this week (ordered Mon → Sun) ─────────────────────────────
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    # Build the last 7 calendar days in order
    last_7: list[DailyHoursItem] = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        label = d.strftime("%a")
        last_7.append(DailyHoursItem(day=label, hours=round(daily_minutes.get(label, 0.0), 1)))

    # ── Percentage changes ────────────────────────────────────────────────────
    def pct_change(current: float, previous: float) -> float:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    hours_change_pct_week = pct_change(total_minutes_this_week / 60, prev_week_minutes / 60)
    sessions_change_pct_month = pct_change(sessions_this_month, sessions_prev_month)

    # ── Library summary ───────────────────────────────────────────────────────
    library_entries = (
        db.query(LibraryEntry)
        .filter(LibraryEntry.user_id == user_id)
        .all()
    )
    games_completed = sum(1 for e in library_entries if e.status == LibraryStatus.COMPLETED)
    games_in_backlog = sum(1 for e in library_entries if e.status == LibraryStatus.BACKLOG)
    games_playing   = sum(1 for e in library_entries if e.status == LibraryStatus.PLAYING)

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
        dominant_emotion_this_month=None,
        emotion_coverage_pct=None,
    )


# ─── Streak helpers ───────────────────────────────────────────────────────────

def _compute_streaks(session_dates: list[date]) -> tuple[int, int]:
    """Return (current_streak_days, longest_streak_days)."""
    if not session_dates:
        return 0, 0

    unique_asc = sorted(set(session_dates))  # oldest → newest
    today = date.today()

    # --- current streak: consecutive days ending today or yesterday ---
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

    # --- longest streak ---
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
