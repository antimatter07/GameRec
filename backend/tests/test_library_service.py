"""
Unit tests for app/services/library_service.py.
DB is mocked — testing business logic: duplicate detection, ownership checks, stats calculation.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Game, User, UserRole
from app.models.library import LibraryEntry, LibraryStatus
from app.schemas.library import LibraryEntryCreate
from app.services.library_service import _sync_overall_rating, add_game, get_stats, get_user_library, remove_game


def _mock_game(id=1, genres=None):
    game = MagicMock()
    game.id = id
    game.genres = genres or [{"id": 1, "name": "Action"}]
    return game


def _mock_entry(id=1, user_id=1, game_id=1, status=LibraryStatus.BACKLOG, rating=None, game=None):
    entry = MagicMock(spec=LibraryEntry)
    entry.id = id
    entry.user_id = user_id
    entry.game_id = game_id
    entry.status = status
    entry.rating = rating
    entry.game = game or _mock_game()
    return entry


@pytest.fixture()
def sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    tables = [User.__table__, Game.__table__, LibraryEntry.__table__]
    for table in tables:
        table.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        for table in reversed(tables):
            table.drop(engine)
        engine.dispose()


def _insert_library_entry(
    db,
    *,
    user_id: int,
    game_id: int,
    rawg_id: int,
    name: str,
    status: LibraryStatus,
    added_at: datetime,
):
    game = Game(
        id=game_id,
        rawg_id=rawg_id,
        name=name,
        slug=f"game-{game_id}",
        genres=[],
        platforms=[],
        tags=[],
        screenshots=[],
    )
    entry = LibraryEntry(
        user_id=user_id,
        game_id=game_id,
        status=status,
        added_at=added_at,
        updated_at=added_at,
    )
    db.add(game)
    db.add(entry)
    return entry


# ── add_game ───────────────────────────────────────────────────────────────────

def test_add_game_raises_404_when_game_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        add_game(db, user_id=1, entry_in=LibraryEntryCreate(game_id=99, status=LibraryStatus.BACKLOG))

    assert exc.value.status_code == 404


def test_add_game_raises_409_when_already_in_library():
    db = MagicMock()
    # First query returns the game, second returns an existing library entry
    db.query.return_value.filter.return_value.first.side_effect = [
        _mock_game(id=1),
        _mock_entry(game_id=1),
    ]

    with pytest.raises(HTTPException) as exc:
        add_game(db, user_id=1, entry_in=LibraryEntryCreate(game_id=1, status=LibraryStatus.BACKLOG))

    assert exc.value.status_code == 409


# ── remove_game ────────────────────────────────────────────────────────────────

def test_remove_game_raises_404_when_entry_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        remove_game(db, user_id=1, entry_id=99)

    assert exc.value.status_code == 404


def test_remove_game_raises_403_when_not_owner():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _mock_entry(user_id=2)

    with pytest.raises(HTTPException) as exc:
        remove_game(db, user_id=1, entry_id=1)

    assert exc.value.status_code == 403


def test_remove_game_deletes_and_commits():
    db = MagicMock()
    entry = _mock_entry(user_id=1)
    db.query.return_value.filter.return_value.first.return_value = entry

    remove_game(db, user_id=1, entry_id=1)

    db.delete.assert_called_once_with(entry)
    db.commit.assert_called_once()


# ── get_stats ──────────────────────────────────────────────────────────────────

def test_get_stats_empty_library():
    with patch("app.services.library_service.get_user_library", return_value=[]):
        result = get_stats(MagicMock(), user_id=1)

    assert result["total_games"] == 0
    assert result["avg_rating"] is None
    assert result["top_genres"] == []


def test_get_stats_counts_by_status():
    entries = [
        _mock_entry(status=LibraryStatus.COMPLETED),
        _mock_entry(status=LibraryStatus.PLAYING),
        _mock_entry(status=LibraryStatus.REPLAYING),
        _mock_entry(status=LibraryStatus.WISHLIST),
        _mock_entry(status=LibraryStatus.BACKLOG),
        _mock_entry(status=LibraryStatus.BACKLOG),
    ]
    with patch("app.services.library_service.get_user_library", return_value=entries):
        result = get_stats(MagicMock(), user_id=1)

    assert result["total_games"] == 6
    assert result["by_status"]["completed"] == 1
    assert result["by_status"]["playing"] == 1
    assert result["by_status"]["replaying"] == 1
    assert result["by_status"]["wishlist"] == 1
    assert result["by_status"]["backlog"] == 2


def test_sync_overall_rating_creates_game_rating_when_missing():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    _sync_overall_rating(db, user_id=1, game_id=2, rating_value=4.5)

    created = db.add.call_args.args[0]
    assert created.user_id == 1
    assert created.game_id == 2
    assert created.overall == 4.5


def test_sync_overall_rating_updates_existing_game_rating():
    db = MagicMock()
    existing = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = existing

    _sync_overall_rating(db, user_id=1, game_id=2, rating_value=3.0)

    assert existing.overall == 3.0
    db.add.assert_not_called()


def test_get_stats_calculates_average_rating():
    entries = [
        _mock_entry(status=LibraryStatus.COMPLETED, rating=4.0),
        _mock_entry(status=LibraryStatus.COMPLETED, rating=2.0),
        _mock_entry(status=LibraryStatus.BACKLOG, rating=None),  # unrated, excluded from avg
    ]
    with patch("app.services.library_service.get_user_library", return_value=entries):
        result = get_stats(MagicMock(), user_id=1)

    assert result["avg_rating"] == 3.0


def test_get_stats_top_genres_sorted_by_count():
    rpg_game = _mock_game(genres=[{"id": 1, "name": "RPG"}])
    action_game = _mock_game(genres=[{"id": 2, "name": "Action"}])
    entries = [
        _mock_entry(game=rpg_game),
        _mock_entry(game=rpg_game),
        _mock_entry(game=action_game),
    ]
    with patch("app.services.library_service.get_user_library", return_value=entries):
        result = get_stats(MagicMock(), user_id=1)

    assert result["top_genres"][0]["genre"] == "RPG"
    assert result["top_genres"][0]["count"] == 2


def test_get_user_library_filters_by_title_search(sqlite_db):
    user = User(email="player@example.com", hashed_password="pw", display_name="Player", role=UserRole.BASIC)
    sqlite_db.add(user)
    sqlite_db.flush()

    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=1,
        rawg_id=101,
        name="Mass Effect",
        status=LibraryStatus.BACKLOG,
        added_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=2,
        rawg_id=102,
        name="Stardew Valley",
        status=LibraryStatus.WISHLIST,
        added_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    sqlite_db.commit()

    results = get_user_library(sqlite_db, user.id, search="  effect  ")

    assert [entry.game.name for entry in results] == ["Mass Effect"]


def test_get_user_library_filters_by_status(sqlite_db):
    user = User(email="player2@example.com", hashed_password="pw", display_name="Player 2", role=UserRole.BASIC)
    sqlite_db.add(user)
    sqlite_db.flush()

    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=1,
        rawg_id=201,
        name="Hades",
        status=LibraryStatus.PLAYING,
        added_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=2,
        rawg_id=202,
        name="Celeste",
        status=LibraryStatus.COMPLETED,
        added_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    sqlite_db.commit()

    results = get_user_library(sqlite_db, user.id, status_filter="playing")

    assert [entry.status for entry in results] == [LibraryStatus.PLAYING]
    assert [entry.game.name for entry in results] == ["Hades"]


def test_get_user_library_all_status_keeps_all_entries(sqlite_db):
    user = User(email="player3@example.com", hashed_password="pw", display_name="Player 3", role=UserRole.BASIC)
    sqlite_db.add(user)
    sqlite_db.flush()

    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=1,
        rawg_id=301,
        name="Portal 2",
        status=LibraryStatus.BACKLOG,
        added_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=2,
        rawg_id=302,
        name="Outer Wilds",
        status=LibraryStatus.WISHLIST,
        added_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    sqlite_db.commit()

    results = get_user_library(sqlite_db, user.id, status_filter="all")

    assert len(results) == 2


def test_get_user_library_sorts_by_newest_added_first(sqlite_db):
    user = User(email="player4@example.com", hashed_password="pw", display_name="Player 4", role=UserRole.BASIC)
    sqlite_db.add(user)
    sqlite_db.flush()

    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=1,
        rawg_id=401,
        name="Disco Elysium",
        status=LibraryStatus.BACKLOG,
        added_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=2,
        rawg_id=402,
        name="Balatro",
        status=LibraryStatus.BACKLOG,
        added_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )
    sqlite_db.commit()

    results = get_user_library(sqlite_db, user.id, sort="added_at_desc")

    assert [entry.game.name for entry in results] == ["Balatro", "Disco Elysium"]


def test_get_user_library_sorts_by_oldest_added_first(sqlite_db):
    user = User(email="player5@example.com", hashed_password="pw", display_name="Player 5", role=UserRole.BASIC)
    sqlite_db.add(user)
    sqlite_db.flush()

    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=1,
        rawg_id=501,
        name="Slay the Spire",
        status=LibraryStatus.BACKLOG,
        added_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=2,
        rawg_id=502,
        name="Animal Well",
        status=LibraryStatus.BACKLOG,
        added_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    sqlite_db.commit()

    results = get_user_library(sqlite_db, user.id, sort="added_at_asc")

    assert [entry.game.name for entry in results] == ["Animal Well", "Slay the Spire"]


def test_get_user_library_sorts_by_status_then_newest_added(sqlite_db):
    user = User(email="player6@example.com", hashed_password="pw", display_name="Player 6", role=UserRole.BASIC)
    sqlite_db.add(user)
    sqlite_db.flush()

    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=1,
        rawg_id=601,
        name="Halo Infinite",
        status=LibraryStatus.COMPLETED,
        added_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=2,
        rawg_id=602,
        name="Final Fantasy VII Rebirth",
        status=LibraryStatus.PLAYING,
        added_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=3,
        rawg_id=603,
        name="Metaphor: ReFantazio",
        status=LibraryStatus.PLAYING,
        added_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )
    _insert_library_entry(
        sqlite_db,
        user_id=user.id,
        game_id=4,
        rawg_id=604,
        name="Prince of Persia: The Lost Crown",
        status=LibraryStatus.WISHLIST,
        added_at=datetime(2024, 1, 4, tzinfo=timezone.utc),
    )
    sqlite_db.commit()

    results = get_user_library(sqlite_db, user.id, sort="status")

    assert [entry.game.name for entry in results] == [
        "Metaphor: ReFantazio",
        "Final Fantasy VII Rebirth",
        "Prince of Persia: The Lost Crown",
        "Halo Infinite",
    ]
