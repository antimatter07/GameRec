from datetime import date, timedelta

from app.services.game_filter import passes_game_filters


def _base_game(**overrides):
    game = {
        "id": 123,
        "slug": "test-game",
        "name": "Test Game",
        "released": "2020-01-01",
        "description_raw": "A real game with enough information to be considered credible.",
        "background_image": "https://example.com/cover.jpg",
        "genres": [{"id": 1, "name": "Adventure"}],
        "platforms": [{"platform": {"id": 4, "name": "PC"}}],
        "tags": [],
        "rating": 3.0,
        "ratings_count": 0,
        "added": 0,
        "metacritic": None,
        "playtime": 0,
    }
    game.update(overrides)
    return game


def test_recognized_indie_with_sparse_ratings_survives():
    passes, reason = passes_game_filters(_base_game(rating=4.2, ratings_count=5, added=12))

    assert passes is True
    assert reason == "cult_rating"


def test_aaa_with_metacritic_survives():
    passes, reason = passes_game_filters(_base_game(metacritic=87, ratings_count=0, added=0))

    assert passes is True
    assert reason == "metacritic"


def test_no_traction_placeholder_drops():
    passes, reason = passes_game_filters(
        _base_game(
            description_raw=None,
            background_image=None,
            genres=[],
            platforms=[],
            tags=[{"id": 1, "name": "Action"}],
            ratings_count=0,
            added=0,
            playtime=0,
            metacritic=None,
        )
    )

    assert passes is False
    assert reason == "zero_traction"


def test_missing_release_date_with_real_metadata_survives():
    passes, reason = passes_game_filters(_base_game(released=None, added=45))

    assert passes is True
    assert reason == "credible_metadata"


def test_future_release_drops():
    future = (date.today() + timedelta(days=30)).isoformat()
    passes, reason = passes_game_filters(_base_game(released=future, added=1000))

    assert passes is False
    assert reason == "future_release"


def test_demo_tag_drops():
    passes, reason = passes_game_filters(
        _base_game(tags=[{"id": 1, "name": "Demo", "slug": "demo"}], added=1000)
    )

    assert passes is False
    assert reason == "excluded_tag:demo"


def test_allowlisted_game_survives_sparse_metadata():
    passes, reason = passes_game_filters(
        {
            "id": 999,
            "slug": "graveyard-keeper",
            "name": "Graveyard Keeper",
            "released": "2018-08-15",
            "genres": [],
            "tags": [],
            "platforms": [],
        }
    )

    assert passes is True
    assert reason == "allowlisted"
