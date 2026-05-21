from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Game, GameExternalId, LibraryEntry, User, UserRole
from app.models.library import LibraryStatus
from app.services.steam_import_service import (
    import_steam_library,
    normalize_game_title,
    sequel_tokens,
    _score_candidate,
)
from app.utils.steam_client import SteamOwnedGame
from app.utils.steam_client import extract_steam_identifier


class FakeSteamClient:
    def __init__(self, games: list[SteamOwnedGame]):
        self.games = games

    def resolve_steam_id(self, steam_profile: str) -> str:
        return "76561198000000000"

    def ensure_public_profile(self, steam_id: str) -> dict:
        return {"personaname": "Test Player", "communityvisibilitystate": 3}

    def get_owned_games(self, steam_id: str) -> list[SteamOwnedGame]:
        return self.games


def _sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    tables = [User.__table__, Game.__table__, GameExternalId.__table__, LibraryEntry.__table__]
    for table in tables:
        table.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return engine, session, tables


def _add_user(db) -> User:
    user = User(email="steam@example.com", hashed_password="pw", display_name="Steam", role=UserRole.BASIC)
    db.add(user)
    db.flush()
    return user


def _add_game(db, *, game_id: int, rawg_id: int, name: str, ratings_count: int = 0) -> Game:
    game = Game(
        id=game_id,
        rawg_id=rawg_id,
        name=name,
        slug=f"game-{game_id}",
        genres=[],
        platforms=[],
        tags=[],
        screenshots=[],
        ratings_count=ratings_count,
    )
    db.add(game)
    db.flush()
    return game


def test_normalize_title_strips_edition_words_and_converts_roman_numerals():
    assert normalize_game_title("Dark Souls™ II: Scholar of the First Sin Edition") == "dark souls 2 scholar of the first sin"
    assert normalize_game_title("Game Dev Tycoon") == "game dev tycoon"
    assert normalize_game_title("Control Game of the Year Edition") == "control"
    assert sequel_tokens("Dark Souls III") == {3}


def test_extract_steam_identifier_accepts_ids_urls_and_vanity_names():
    assert extract_steam_identifier("76561198000000000") == "76561198000000000"
    assert extract_steam_identifier("https://steamcommunity.com/profiles/76561198000000000/") == "76561198000000000"
    assert extract_steam_identifier("https://steamcommunity.com/id/cool_player/") == "cool_player"


def test_fuzzy_score_rejects_conflicting_sequels():
    assert _score_candidate("Dark Souls 2", "Dark Souls 3") == 0
    assert _score_candidate("Dark Souls II", "Dark Souls 2") >= 92


def test_import_adds_confident_matches_as_backlog_and_preserves_unmatched():
    engine, db, tables = _sqlite_db()
    try:
        user = _add_user(db)
        _add_game(db, game_id=1, rawg_id=101, name="Dark Souls 2", ratings_count=100)

        result = import_steam_library(
            db,
            user.id,
            "76561198000000000",
            client=FakeSteamClient(
                [
                    SteamOwnedGame(appid=335300, name="Dark Souls II", playtime_forever=123, rtime_last_played=1700000000),
                    SteamOwnedGame(appid=999999, name="Totally Missing Game"),
                ]
            ),
        )

        entries = db.query(LibraryEntry).all()
        assert len(entries) == 1
        assert entries[0].status == LibraryStatus.BACKLOG
        assert entries[0].steam_app_id == 335300
        assert entries[0].steam_playtime_forever_minutes == 123
        assert entries[0].steam_last_played_at.replace(tzinfo=timezone.utc) == datetime.fromtimestamp(1700000000, tz=timezone.utc)
        assert len(result["added"]) == 1
        assert len(result["unmatched"]) == 1
        assert db.query(Game).count() == 1
    finally:
        db.close()
        for table in reversed(tables):
            table.drop(engine)
        engine.dispose()


def test_import_updates_existing_entry_metadata_without_removing_other_library_games():
    engine, db, tables = _sqlite_db()
    try:
        user = _add_user(db)
        matched = _add_game(db, game_id=1, rawg_id=101, name="Hades")
        other = _add_game(db, game_id=2, rawg_id=102, name="PlayStation Exclusive")
        db.add(LibraryEntry(user_id=user.id, game_id=matched.id, status=LibraryStatus.COMPLETED))
        db.add(LibraryEntry(user_id=user.id, game_id=other.id, status=LibraryStatus.BACKLOG))
        db.commit()

        result = import_steam_library(
            db,
            user.id,
            "76561198000000000",
            client=FakeSteamClient([SteamOwnedGame(appid=1145360, name="Hades", playtime_forever=500)]),
        )

        entries = db.query(LibraryEntry).order_by(LibraryEntry.game_id).all()
        assert len(entries) == 2
        assert entries[0].status == LibraryStatus.COMPLETED
        assert entries[0].steam_app_id == 1145360
        assert entries[1].game_id == other.id
        assert entries[1].steam_app_id is None
        assert len(result["already_in_library"]) == 1
        assert len(result["added"]) == 0
    finally:
        db.close()
        for table in reversed(tables):
            table.drop(engine)
        engine.dispose()
