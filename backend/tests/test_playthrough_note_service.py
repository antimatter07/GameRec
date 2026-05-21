from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Game, PlaythroughNote, User, UserRole
from app.models.library import LibraryEntry, LibraryStatus
from app.schemas.journal import PlaythroughNoteCreate, PlaythroughNoteUpdate
from app.services.journal_service import create_note, list_notes, update_note


@pytest.fixture()
def sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    tables = [User.__table__, Game.__table__, LibraryEntry.__table__, PlaythroughNote.__table__]
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


def _seed_user_game_and_entry(db):
    user = User(
        id=1,
        email="player@example.com",
        hashed_password="secret",
        display_name="Player One",
        role=UserRole.BASIC,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    game = Game(
        id=10,
        rawg_id=1010,
        name="Elden Ring",
        slug="elden-ring",
        genres=[],
        platforms=[],
        tags=[],
        screenshots=[],
    )
    entry = LibraryEntry(
        id=99,
        user_id=1,
        game_id=10,
        status=LibraryStatus.PLAYING,
        added_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add_all([user, game, entry])
    db.commit()


def test_create_note_returns_joined_game_metadata(sqlite_db):
    _seed_user_game_and_entry(sqlite_db)

    note = create_note(
        sqlite_db,
        user_id=1,
        payload=PlaythroughNoteCreate(
            game_id=10,
            library_entry_id=99,
            kind="goal",
            title="Find Blaidd before going north",
            body="Check Mistwood ruins first.",
            remind_next_session=True,
            pinned=True,
        ),
    )

    assert note.game_title == "Elden Ring"
    assert note.kind == "goal"
    assert note.remind_next_session is True
    assert note.pinned is True


def test_update_note_marks_done_and_list_filters_by_status(sqlite_db):
    _seed_user_game_and_entry(sqlite_db)

    created = create_note(
        sqlite_db,
        user_id=1,
        payload=PlaythroughNoteCreate(
            game_id=10,
            library_entry_id=99,
            kind="recipe",
            title="Potion mix",
            body="x + y + z",
        ),
    )

    updated = update_note(
        sqlite_db,
        user_id=1,
        note_id=created.id,
        payload=PlaythroughNoteUpdate(status="done"),
    )

    done_notes = list_notes(sqlite_db, user_id=1, status_value="done", per_page=20)

    assert updated.status == "done"
    assert updated.completed_at is not None
    assert done_notes.total == 1
    assert done_notes.items[0].title == "Potion mix"
