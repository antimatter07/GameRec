from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.journal import SessionLog
from app.schemas.journal import JournalStats, SessionLogCreate, SessionLogUpdate, TopGenreItem


def _load_session(db: Session, session_id: int, user_id: int) -> SessionLog:
    """Fetch a session by id, verifying ownership. Raises 404/403 as appropriate."""
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return session


def _with_game(db: Session, session_id: int) -> SessionLog:
    """Re-fetch a session with game relationship loaded."""
    return (
        db.query(SessionLog)
        .filter(SessionLog.id == session_id)
        .options(joinedload(SessionLog.game))
        .first()
    )


def create_session(db: Session, user_id: int, payload: SessionLogCreate) -> SessionLog:
    game = db.query(Game).filter(Game.id == payload.game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    entry = SessionLog(user_id=user_id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _with_game(db, entry.id)


def list_sessions(
    db: Session,
    user_id: int,
    game_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
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
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "results": results}


def update_session(
    db: Session, user_id: int, session_id: int, payload: SessionLogUpdate
) -> SessionLog:
    session = _load_session(db, session_id, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    db.commit()
    return _with_game(db, session.id)


def delete_session(db: Session, user_id: int, session_id: int) -> None:
    session = _load_session(db, session_id, user_id)
    db.delete(session)
    db.commit()


def get_stats(db: Session, user_id: int) -> JournalStats:
    all_sessions = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id)
        .options(joinedload(SessionLog.game))
        .all()
    )

    now = datetime.now(timezone.utc)
    current_month = now.month
    current_year  = now.year

    total_minutes_all_time   = 0
    total_minutes_this_month = 0
    games_this_month: set[int] = set()
    genre_minutes: dict[str, float] = defaultdict(float)
    session_dates: list[date] = []

    for s in all_sessions:
        minutes = s.duration_minutes or 0
        started = s.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        session_dates.append(started.date())
        total_minutes_all_time += minutes

        if started.month == current_month and started.year == current_year:
            total_minutes_this_month += minutes
            games_this_month.add(s.game_id)
            for genre in (s.game.genres or []):
                genre_minutes[genre["name"]] += minutes / 60

    current_streak, longest_streak = _compute_streaks(session_dates)

    top_genres = sorted(
        [TopGenreItem(genre=name, hours=round(hours, 1)) for name, hours in genre_minutes.items()],
        key=lambda x: x.hours,
        reverse=True,
    )[:5]

    sessions_this_month = sum(
        1 for s in all_sessions
        if (
            (s.started_at if s.started_at.tzinfo else s.started_at.replace(tzinfo=timezone.utc)).month == current_month
            and (s.started_at if s.started_at.tzinfo else s.started_at.replace(tzinfo=timezone.utc)).year == current_year
        )
    )

    return JournalStats(
        total_hours_all_time=round(total_minutes_all_time / 60, 1),
        total_hours_this_month=round(total_minutes_this_month / 60, 1),
        sessions_this_month=sessions_this_month,
        games_played_this_month=len(games_this_month),
        top_genres_this_month=top_genres,
        current_streak_days=current_streak,
        longest_streak_days=longest_streak,
    )


def get_feed(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> dict:
    query = (
        db.query(SessionLog)
        .filter(SessionLog.user_id == user_id)
        .options(joinedload(SessionLog.game))
        .order_by(SessionLog.started_at.desc())
    )
    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "results": results}


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
    longest = 1
    run = 1
    for i in range(1, len(unique_asc)):
        if (unique_asc[i] - unique_asc[i - 1]).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    return current, longest
