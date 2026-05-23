from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.permissions import can_access_ai_picks
from app.models.game import Game
from app.models.library import LibraryEntry, LibraryStatus
from app.models.recommendation import Recommendation, RecommendationItem, RecommendationKind, RecommendationStatus
from app.models.user import User, UserRole
from app.services.ai_picks_service import (
    AIPickCandidate,
    AIPicksProposal,
    CompactTasteSummary,
    TasteDossier,
    build_compact_taste_summary,
    generate_ai_picks_for_recommendation,
    request_ai_picks_refresh,
    resolve_ai_pick_candidates,
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


@pytest.fixture()
def sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    tables = [
        User.__table__,
        Game.__table__,
        LibraryEntry.__table__,
        Recommendation.__table__,
        RecommendationItem.__table__,
    ]
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


def _add_user(db, user_id: int = 1):
    user = User(id=user_id, email=f"user-{user_id}@example.com", role=UserRole.BASIC)
    db.add(user)
    db.flush()
    return user


def _add_game(
    db,
    *,
    game_id: int,
    rawg_id: int,
    name: str,
    slug: str,
    ratings_count: int = 100,
    rating: float = 4.0,
    metacritic: int | None = 80,
):
    game = Game(
        id=game_id,
        rawg_id=rawg_id,
        name=name,
        slug=slug,
        rating=rating,
        ratings_count=ratings_count,
        metacritic=metacritic,
        genres=[],
        platforms=[],
        tags=[],
        screenshots=[],
    )
    db.add(game)
    db.flush()
    return game


def _candidate(title: str, *, slug: str | None = None, confidence: float = 0.8):
    return AIPickCandidate(
        title=title,
        slug=slug,
        explanation=f"{title} fits your taste.",
        confidence=confidence,
        because_you_liked=["Mass Effect 2"],
    )


def _proposal(*candidates: AIPickCandidate):
    return AIPicksProposal(
        taste_summary="You like thoughtful RPGs.",
        candidates=list(candidates),
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


def test_resolve_ai_pick_candidates_matches_exact_slug(sqlite_db):
    _add_user(sqlite_db)
    game = _add_game(sqlite_db, game_id=1, rawg_id=101, name="Citizen Sleeper", slug="citizen-sleeper")

    resolved, dropped = resolve_ai_pick_candidates(
        1,
        _proposal(_candidate("Some Other Text", slug="citizen-sleeper")),
        sqlite_db,
    )

    assert [pick.game.id for pick in resolved] == [game.id]
    assert resolved[0].match_reason == "exact_slug"
    assert dropped == []


def test_resolve_ai_pick_candidates_matches_exact_normalized_title(sqlite_db):
    _add_user(sqlite_db)
    game = _add_game(sqlite_db, game_id=1, rawg_id=101, name="Control", slug="control")

    resolved, dropped = resolve_ai_pick_candidates(
        1,
        _proposal(_candidate("Control Game of the Year Edition")),
        sqlite_db,
    )

    assert [pick.game.id for pick in resolved] == [game.id]
    assert resolved[0].match_reason == "exact_title"
    assert dropped == []


def test_resolve_ai_pick_candidates_matches_high_confidence_fuzzy_title(sqlite_db):
    _add_user(sqlite_db)
    game = _add_game(sqlite_db, game_id=1, rawg_id=101, name="Dark Souls 2", slug="dark-souls-2")

    resolved, dropped = resolve_ai_pick_candidates(
        1,
        _proposal(_candidate("Dark Souls II")),
        sqlite_db,
    )

    assert [pick.game.id for pick in resolved] == [game.id]
    assert resolved[0].match_reason in {"exact_title", "fuzzy_title"}
    assert dropped == []


def test_resolve_ai_pick_candidates_rejects_sequel_conflict(sqlite_db):
    _add_user(sqlite_db)
    _add_game(sqlite_db, game_id=1, rawg_id=101, name="Dark Souls 3", slug="dark-souls-3")

    resolved, dropped = resolve_ai_pick_candidates(
        1,
        _proposal(_candidate("Dark Souls 2")),
        sqlite_db,
    )

    assert resolved == []
    assert dropped[0].reason in {"low_confidence_match", "not_found"}


def test_resolve_ai_pick_candidates_drops_owned_duplicate_and_unresolved(sqlite_db):
    _add_user(sqlite_db)
    owned = _add_game(sqlite_db, game_id=1, rawg_id=101, name="Owned RPG", slug="owned-rpg")
    kept = _add_game(sqlite_db, game_id=2, rawg_id=102, name="Pentiment", slug="pentiment")
    sqlite_db.add(LibraryEntry(user_id=1, game_id=owned.id, status=LibraryStatus.COMPLETED))
    sqlite_db.commit()

    resolved, dropped = resolve_ai_pick_candidates(
        1,
        _proposal(
            _candidate("Owned RPG"),
            _candidate("Pentiment"),
            _candidate("Pentiment", slug="pentiment"),
            _candidate("Totally Missing Game"),
        ),
        sqlite_db,
    )

    assert [pick.game.id for pick in resolved] == [kept.id]
    assert [drop.reason for drop in dropped] == ["owned", "duplicate", "low_confidence_match"]


def test_generate_ai_picks_stores_partial_resolved_results(monkeypatch, sqlite_db):
    _add_user(sqlite_db)
    game = _add_game(sqlite_db, game_id=1, rawg_id=101, name="Pentiment", slug="pentiment")
    recommendation = Recommendation(
        user_id=1,
        kind=RecommendationKind.AI_PICKS,
        status=RecommendationStatus.PENDING,
    )
    sqlite_db.add(recommendation)
    sqlite_db.commit()

    monkeypatch.setattr(
        "app.services.ai_picks_service.build_taste_dossier",
        lambda _user_id, _db: (
            CompactTasteSummary(top_genres=["Adventure"]),
            TasteDossier(taste_summary="Narrative-heavy games fit you.", preferred_tags=["Story Rich"]),
        ),
    )
    monkeypatch.setattr(
        "app.services.ai_picks_service._generate_proposal_once",
        lambda _dossier, stricter=False: _proposal(
            _candidate("Pentiment", confidence=0.93),
            _candidate("Totally Missing Game", confidence=0.8),
        ),
    )
    monkeypatch.setattr("app.services.ai_picks_service._clear_dirty_flag", lambda _user_id: None)

    result = generate_ai_picks_for_recommendation(recommendation.id, 1, sqlite_db)

    assert result.status == RecommendationStatus.READY
    assert result.summary == "You like thoughtful RPGs."
    assert result.profile_snapshot["resolved_game_ids"] == [game.id]
    assert result.profile_snapshot["dropped_candidates"][0]["reason"] == "low_confidence_match"
    assert len(result.items) == 1
    assert result.items[0].game_id == game.id
    assert result.items[0].rank == 1
    assert result.items[0].score == pytest.approx(0.93)
    assert result.items[0].confidence == pytest.approx(0.93)
    assert result.items[0].explanation == "Pentiment fits your taste."
    assert result.items[0].because_you_liked == ["Mass Effect 2"]


def test_generate_ai_picks_fails_when_zero_games_resolve(monkeypatch, sqlite_db):
    _add_user(sqlite_db)
    recommendation = Recommendation(
        user_id=1,
        kind=RecommendationKind.AI_PICKS,
        status=RecommendationStatus.PENDING,
    )
    sqlite_db.add(recommendation)
    sqlite_db.commit()

    monkeypatch.setattr(
        "app.services.ai_picks_service.build_taste_dossier",
        lambda _user_id, _db: (
            CompactTasteSummary(top_genres=["Adventure"]),
            TasteDossier(taste_summary="Narrative-heavy games fit you.", preferred_tags=["Story Rich"]),
        ),
    )
    monkeypatch.setattr(
        "app.services.ai_picks_service._generate_proposal_once",
        lambda _dossier, stricter=False: _proposal(_candidate("Totally Missing Game")),
    )

    with pytest.raises(ValueError, match="could not match any suggested games"):
        generate_ai_picks_for_recommendation(recommendation.id, 1, sqlite_db)

    sqlite_db.refresh(recommendation)
    assert recommendation.status == RecommendationStatus.FAILED
    assert recommendation.profile_snapshot["resolved_game_ids"] == []


def test_request_ai_picks_refresh_forces_new_batch_when_ready_batch_is_fresh(monkeypatch, sqlite_db):
    _add_user(sqlite_db)
    ready = Recommendation(
        user_id=1,
        kind=RecommendationKind.AI_PICKS,
        status=RecommendationStatus.READY,
        summary="Existing fresh batch.",
    )
    sqlite_db.add(ready)
    sqlite_db.commit()

    monkeypatch.setattr("app.services.ai_picks_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.ai_picks_service.build_compact_taste_summary",
        lambda _user_id, _db: CompactTasteSummary(top_genres=["Adventure"]),
    )
    monkeypatch.setattr("app.services.ai_picks_service._is_stale", lambda _recommendation, _user_id: False)

    recommendation, should_enqueue = request_ai_picks_refresh(1, sqlite_db)

    assert should_enqueue is True
    assert recommendation.id != ready.id
    assert recommendation.status == RecommendationStatus.PENDING
    assert recommendation.summary == "AI Picks are being generated."


def test_request_ai_picks_refresh_reuses_existing_pending_batch(monkeypatch, sqlite_db):
    _add_user(sqlite_db)
    pending = Recommendation(
        user_id=1,
        kind=RecommendationKind.AI_PICKS,
        status=RecommendationStatus.PENDING,
        summary="AI Picks are being generated.",
    )
    sqlite_db.add(pending)
    sqlite_db.commit()

    monkeypatch.setattr("app.services.ai_picks_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.ai_picks_service.build_compact_taste_summary",
        lambda _user_id, _db: CompactTasteSummary(top_genres=["Adventure"]),
    )

    recommendation, should_enqueue = request_ai_picks_refresh(1, sqlite_db)

    assert should_enqueue is False
    assert recommendation.id == pending.id


def test_can_access_ai_picks_respects_feature_flag(monkeypatch):
    user = SimpleNamespace(role=UserRole.BASIC)

    monkeypatch.setattr("app.core.permissions.settings.AI_PICKS_REQUIRE_PREMIUM", False)
    assert can_access_ai_picks(user) is True

    monkeypatch.setattr("app.core.permissions.settings.AI_PICKS_REQUIRE_PREMIUM", True)
    assert can_access_ai_picks(user) is False
