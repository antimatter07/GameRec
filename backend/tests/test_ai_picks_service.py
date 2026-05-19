from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.permissions import can_access_ai_picks
from app.models.library import LibraryStatus
from app.models.user import UserRole
from app.services.ai_picks_service import (
    AIPick,
    AIPicksSelection,
    build_compact_taste_summary,
    _validate_selection,
)


def _entry_query(entries):
    query = MagicMock()
    query.options.return_value.filter.return_value.all.return_value = entries
    return query


def _rating_query(ratings):
    query = MagicMock()
    query.filter.return_value.all.return_value = ratings
    return query


def _session_query(sessions):
    query = MagicMock()
    query.filter.return_value.options.return_value.order_by.return_value.all.return_value = sessions
    return query


def _game(name: str, *, genres=None, tags=None, platforms=None, released_year=2020, hltb=18.0):
    return SimpleNamespace(
        name=name,
        genres=genres or [],
        tags=tags or [],
        platforms=platforms or [],
        released=SimpleNamespace(year=released_year),
        hltb_main_hours=hltb,
        playtime=None,
    )


def test_build_compact_taste_summary_raises_without_any_user_signal():
    db = MagicMock()
    db.query.side_effect = [
        _entry_query([]),
        _rating_query([]),
        _session_query([]),
    ]

    with pytest.raises(ValueError):
        build_compact_taste_summary(user_id=1, db=db)


def test_build_compact_taste_summary_derives_preferences_from_library_and_journal():
    favorite_game = _game(
        "Mass Effect 2",
        genres=[{"name": "RPG"}],
        tags=[{"name": "Story Rich", "language": "eng"}],
        platforms=[{"name": "PC"}],
        hltb=25.0,
    )
    dropped_game = _game(
        "Arena Grind",
        genres=[{"name": "Action"}],
        tags=[{"name": "PvP", "language": "eng"}],
        platforms=[{"name": "PC"}],
        hltb=8.0,
    )
    entries = [
        SimpleNamespace(
            game=favorite_game,
            rating=5.0,
            status=LibraryStatus.COMPLETED,
            review="Loved the squad dynamics and choices.",
        ),
        SimpleNamespace(
            game=dropped_game,
            rating=1.5,
            status=LibraryStatus.DROPPED,
            review="Did not enjoy the PvP focus.",
        ),
    ]
    ratings = [
        SimpleNamespace(story=5.0, gameplay=4.0, visuals=4.0, soundtrack=4.0, overall=5.0),
    ]
    sessions = [
        SimpleNamespace(
            notes="Great character banter during the loyalty missions.",
            emotions=["happy", "proud"],
        ),
    ]

    db = MagicMock()
    db.query.side_effect = [
        _entry_query(entries),
        _rating_query(ratings),
        _session_query(sessions),
    ]

    summary = build_compact_taste_summary(user_id=1, db=db)

    assert summary.top_genres[0] == "RPG"
    assert "Story Rich" in summary.top_tags
    assert "PvP" in summary.avoid_tags
    assert summary.story_vs_gameplay == "story-heavy"
    assert "Mass Effect 2" in summary.favorite_games
    assert "Arena Grind" in summary.disliked_games
    assert summary.common_emotions == ["happy", "proud"]


def test_validate_selection_rejects_unknown_ids():
    selection = AIPicksSelection(
        taste_summary="You like thoughtful RPGs.",
        picks=[
            AIPick(game_id=999, explanation="Fits your story-first taste.", confidence=0.8),
        ],
    )

    with pytest.raises(ValueError):
        _validate_selection(selection, candidate_ids={1, 2, 3}, owned_game_ids=set())


def test_can_access_ai_picks_respects_feature_flag(monkeypatch):
    user = SimpleNamespace(role=UserRole.BASIC)

    monkeypatch.setattr("app.core.permissions.settings.AI_PICKS_REQUIRE_PREMIUM", False)
    assert can_access_ai_picks(user) is True

    monkeypatch.setattr("app.core.permissions.settings.AI_PICKS_REQUIRE_PREMIUM", True)
    assert can_access_ai_picks(user) is False
