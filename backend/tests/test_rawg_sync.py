from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.game import Game
from app.models.rawg_sync_state import RawgSeenGame, RawgSyncState
from app.workers.tasks import rawg_sync


class FakeRAWGClient:
    def __init__(self, pages):
        self.pages = pages
        self.detail_calls = 0

    def iter_catalog_pass(self, pass_name, page=1, page_size=40, days_back=60):
        return self.pages.get(page, {"results": [], "next": None})

    def get_game_detail(self, rawg_id):
        self.detail_calls += 1
        return {
            "id": rawg_id,
            "slug": f"game-{rawg_id}",
            "name": f"Game {rawg_id}",
            "description_raw": "A credible game with enough metadata to sync.",
            "released": "2020-01-01",
            "background_image": "https://example.com/cover.jpg",
            "genres": [{"id": 1, "name": "Adventure"}],
            "platforms": [{"platform": {"id": 4, "name": "PC"}}],
            "tags": [],
            "rating": 4.1,
            "ratings_count": 6,
            "added": 25,
            "metacritic": None,
            "playtime": 1,
        }

    def get_game_screenshots(self, rawg_id):
        return {"results": [{"id": 1, "image": "https://example.com/screenshot.jpg"}]}


def _session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Game.__table__.create(bind=engine)
    RawgSyncState.__table__.create(bind=engine)
    RawgSeenGame.__table__.create(bind=engine)
    return sessionmaker(bind=engine)


def test_sync_inserts_accepted_games_and_advances_checkpoint(monkeypatch):
    Session = _session_factory()
    monkeypatch.setattr(rawg_sync, "SessionLocal", Session)
    monkeypatch.setattr(rawg_sync, "_write_status", lambda payload: None)
    fake_client = FakeRAWGClient(
        {
            1: {
                "next": None,
                "results": [
                    {
                        "id": 10,
                        "slug": "game-10",
                        "name": "Game 10",
                        "released": "2020-01-01",
                        "genres": [{"id": 1, "name": "Adventure"}],
                        "platforms": [{"platform": {"id": 4, "name": "PC"}}],
                        "tags": [],
                        "rating": 4.2,
                        "ratings_count": 5,
                        "added": 30,
                        "metacritic": None,
                        "playtime": 1,
                        "background_image": "https://example.com/cover.jpg",
                    }
                ],
            }
        }
    )
    monkeypatch.setattr(rawg_sync, "rawg_client", fake_client)

    result = rawg_sync._run_discovery(pass_names=("popular_added",), max_requests=5)

    db = Session()
    try:
        assert result["accepted"] == 1
        assert db.query(Game).filter(Game.rawg_id == 10).count() == 1
        state = db.get(RawgSyncState, "popular_added")
        assert state.completed is True
        assert state.next_page == 2
        seen = db.get(RawgSeenGame, 10)
        assert seen.accepted is True
        assert fake_client.detail_calls == 0
    finally:
        db.close()


def test_sync_skips_duplicates(monkeypatch):
    Session = _session_factory()
    db = Session()
    db.add(
        Game(
            rawg_id=10,
            name="Existing",
            slug="existing",
            ratings_count=0,
            genres=[],
            platforms=[],
            tags=[],
            screenshots=[],
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(rawg_sync, "SessionLocal", Session)
    monkeypatch.setattr(rawg_sync, "_write_status", lambda payload: None)
    monkeypatch.setattr(
        rawg_sync,
        "rawg_client",
        FakeRAWGClient({1: {"next": None, "results": [{"id": 10, "name": "Existing", "slug": "existing"}]}}),
    )

    result = rawg_sync._run_discovery(pass_names=("popular_added",), max_requests=5)

    assert result["skipped_duplicates"] == 1


def test_sync_deduplicates_repeated_rawg_ids_in_same_page(monkeypatch):
    Session = _session_factory()
    monkeypatch.setattr(rawg_sync, "SessionLocal", Session)
    monkeypatch.setattr(rawg_sync, "_write_status", lambda payload: None)
    monkeypatch.setattr(
        rawg_sync,
        "rawg_client",
        FakeRAWGClient(
            {
                1: {
                    "next": None,
                    "results": [
                        {
                            "id": 10,
                            "slug": "game-10",
                            "name": "Game 10",
                            "released": "2020-01-01",
                            "genres": [{"id": 1, "name": "Adventure"}],
                            "platforms": [{"platform": {"id": 4, "name": "PC"}}],
                            "tags": [],
                            "rating": 4.2,
                            "ratings_count": 5,
                            "added": 30,
                            "metacritic": None,
                            "playtime": 1,
                            "background_image": "https://example.com/cover.jpg",
                        },
                        {
                            "id": 10,
                            "slug": "game-10",
                            "name": "Game 10 Duplicate",
                            "released": "2020-01-01",
                            "genres": [{"id": 1, "name": "Adventure"}],
                            "platforms": [{"platform": {"id": 4, "name": "PC"}}],
                            "tags": [],
                            "rating": 4.2,
                            "ratings_count": 5,
                            "added": 30,
                            "metacritic": None,
                            "playtime": 1,
                            "background_image": "https://example.com/cover.jpg",
                        },
                    ],
                }
            }
        ),
    )

    result = rawg_sync._run_discovery(pass_names=("popular_added",), max_requests=5)

    db = Session()
    try:
        assert result["accepted"] == 1
        assert result["skipped_duplicates"] == 1
        assert db.query(Game).filter(Game.rawg_id == 10).count() == 1
    finally:
        db.close()


def test_sync_does_not_advance_checkpoint_when_budget_exhausted(monkeypatch):
    Session = _session_factory()
    monkeypatch.setattr(rawg_sync, "SessionLocal", Session)
    monkeypatch.setattr(rawg_sync, "_write_status", lambda payload: None)
    monkeypatch.setattr(
        rawg_sync,
        "rawg_client",
        FakeRAWGClient(
            {
                1: {
                    "next": "next-page",
                    "results": [
                        {
                            "id": 10,
                            "slug": "game-10",
                            "name": "Game 10",
                            "released": "2020-01-01",
                            "genres": [{"id": 1, "name": "Adventure"}],
                            "platforms": [{"platform": {"id": 4, "name": "PC"}}],
                            "tags": [],
                            "rating": 4.2,
                            "ratings_count": 5,
                            "added": 30,
                            "background_image": None,
                        }
                    ],
                }
            }
        ),
    )

    result = rawg_sync._run_discovery(pass_names=("popular_added",), max_requests=0)

    db = Session()
    try:
        state = db.get(RawgSyncState, "popular_added")
        assert result["status"] == "stopped"
        assert result["stop_reason"] == "request_budget_exhausted"
        assert state.completed is False
        assert state.next_page == 1
    finally:
        db.close()


def test_discovery_skips_known_rejects_until_recheck(monkeypatch):
    Session = _session_factory()
    db = Session()
    db.add(
        RawgSeenGame(
            rawg_id=10,
            accepted=False,
            reason="zero_traction",
            source_pass="popular_added",
            recheck_after=rawg_sync.datetime.now(rawg_sync.timezone.utc) + rawg_sync.timedelta(days=30),
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(rawg_sync, "SessionLocal", Session)
    monkeypatch.setattr(rawg_sync, "_write_status", lambda payload: None)
    monkeypatch.setattr(
        rawg_sync,
        "rawg_client",
        FakeRAWGClient({1: {"next": None, "results": [{"id": 10, "name": "Nope", "slug": "nope"}]}}),
    )

    result = rawg_sync._run_discovery(pass_names=("popular_added",), max_requests=5)

    assert result["skipped_known_rejects"] == 1


def test_enrichment_fetches_detail_for_inserted_games(monkeypatch):
    Session = _session_factory()
    db = Session()
    db.add(
        Game(
            rawg_id=10,
            name="Game 10",
            slug="game-10",
            description=None,
            ratings_count=5,
            genres=[{"id": 1, "name": "Adventure"}],
            platforms=[],
            tags=[],
            screenshots=[],
        )
    )
    db.commit()
    db.close()

    fake_client = FakeRAWGClient({})
    monkeypatch.setattr(rawg_sync, "SessionLocal", Session)
    monkeypatch.setattr(rawg_sync, "_write_status", lambda payload: None)
    monkeypatch.setattr(rawg_sync, "rawg_client", fake_client)

    result = rawg_sync._run_enrichment(max_requests=1)

    db = Session()
    try:
        game = db.query(Game).filter(Game.rawg_id == 10).first()
        assert result["enriched"] == 1
        assert fake_client.detail_calls == 1
        assert game.description == "A credible game with enough metadata to sync."
    finally:
        db.close()
