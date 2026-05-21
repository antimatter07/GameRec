from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.queue_suggestion_service import (
    QueueSuggestionPosition,
    QueueSuggestionSelection,
    _validate_selection,
    adopt_queue_suggestion,
    compute_queue_fingerprint,
    ensure_queue_suggestion,
    get_queue_suggestion_state,
)


def _queue_row(entry_id: int, position: int, name: str):
    return SimpleNamespace(
        entry_id=entry_id,
        position=position,
        entry=SimpleNamespace(
            id=entry_id,
            rating=4.0,
            game=SimpleNamespace(name=name),
        ),
    )


def test_queue_fingerprint_is_stable_for_same_order():
    assert compute_queue_fingerprint([1, 2, 3]) == compute_queue_fingerprint([1, 2, 3])
    assert compute_queue_fingerprint([1, 2, 3]) != compute_queue_fingerprint([3, 2, 1])


def test_validate_selection_rejects_duplicate_suggested_positions():
    selection = QueueSuggestionSelection(
        overall_explanation="A better rhythm.",
        positions=[
            QueueSuggestionPosition(original_position=1, game_name="Hades", suggested_position=1, reason="Start strong."),
            QueueSuggestionPosition(original_position=2, game_name="Disco Elysium", suggested_position=1, reason="Duplicate slot."),
        ],
    )

    with pytest.raises(ValueError):
        _validate_selection(selection, [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Disco Elysium")])


def test_validate_selection_rejects_mismatched_game_name_for_original_position():
    selection = QueueSuggestionSelection(
        overall_explanation="A better rhythm.",
        positions=[
            QueueSuggestionPosition(original_position=1, game_name="Portal", suggested_position=2, reason="Short and inviting."),
            QueueSuggestionPosition(original_position=2, game_name="Hades", suggested_position=1, reason="Great momentum."),
        ],
    )

    with pytest.raises(ValueError, match="mismatched a game name"):
        _validate_selection(selection, [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Portal")])


def test_validate_selection_rejects_unchanged_order():
    selection = QueueSuggestionSelection(
        overall_explanation="The current order is already strong.",
        positions=[
            QueueSuggestionPosition(original_position=1, game_name="Hades", suggested_position=1, reason="Still a good opener."),
            QueueSuggestionPosition(original_position=2, game_name="Portal", suggested_position=2, reason="Still a good follow-up."),
        ],
    )

    with pytest.raises(ValueError, match="exact original order"):
        _validate_selection(selection, [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Portal")])


def test_get_queue_suggestion_state_returns_noop_for_small_queue(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr("app.services.queue_suggestion_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._load_queue_rows",
        lambda _db, _user_id: [_queue_row(10, 1, "Hades")],
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_overall_with_status",
        lambda _db, _user_id, _status: None,
    )

    state = get_queue_suggestion_state(user_id=1, db=db)

    assert state["suggestion"] is None
    assert state["is_generating"] is False
    assert state["can_generate"] is False
    assert "at least 2 games" in (state["detail"] or "")


def test_get_queue_suggestion_state_keeps_previous_ready_suggestion_when_queue_changes(monkeypatch):
    db = MagicMock()
    previous_ready = SimpleNamespace(
        id=88,
        status="ready",
        queue_fingerprint="old-fingerprint",
        overall_explanation="Keep momentum by alternating longer and shorter games.",
        items=[SimpleNamespace(id=1)],
    )
    monkeypatch.setattr("app.services.queue_suggestion_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._load_queue_rows",
        lambda _db, _user_id: [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Disco Elysium")],
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_for_fingerprint",
        lambda _db, _user_id, _fingerprint: None,
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_overall",
        lambda _db, _user_id: previous_ready,
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_overall_with_status",
        lambda _db, _user_id, status: previous_ready if status == "ready" else None,
    )

    state = get_queue_suggestion_state(user_id=1, db=db)

    assert state["suggestion"] is previous_ready
    assert state["is_stale"] is True
    assert state["is_generating"] is False
    assert state["can_generate"] is True
    assert "still shown" in (state["detail"] or "")


def test_get_queue_suggestion_state_allows_regenerating_matching_ready_suggestion(monkeypatch):
    db = MagicMock()
    matching_ready = SimpleNamespace(
        id=88,
        status="ready",
        queue_fingerprint="current-fingerprint",
        overall_explanation="Keep momentum by alternating longer and shorter games.",
        items=[SimpleNamespace(id=1)],
    )
    monkeypatch.setattr("app.services.queue_suggestion_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._load_queue_rows",
        lambda _db, _user_id: [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Disco Elysium")],
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service.compute_queue_fingerprint",
        lambda _entry_ids: "current-fingerprint",
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_for_fingerprint",
        lambda _db, _user_id, _fingerprint: matching_ready,
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_overall",
        lambda _db, _user_id: matching_ready,
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_overall_with_status",
        lambda _db, _user_id, status: matching_ready if status == "ready" else None,
    )

    state = get_queue_suggestion_state(user_id=1, db=db)

    assert state["suggestion"] is matching_ready
    assert state["is_stale"] is False
    assert state["is_generating"] is False
    assert state["can_generate"] is True


def test_get_queue_suggestion_state_keeps_previous_ready_suggestion_while_refresh_is_pending(monkeypatch):
    db = MagicMock()
    previous_ready = SimpleNamespace(
        id=88,
        status="ready",
        queue_fingerprint="old-fingerprint",
        overall_explanation="Keep momentum by alternating longer and shorter games.",
        items=[SimpleNamespace(id=1)],
    )
    current_pending = SimpleNamespace(
        id=99,
        status="pending",
        queue_fingerprint="current-fingerprint",
    )
    monkeypatch.setattr("app.services.queue_suggestion_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._load_queue_rows",
        lambda _db, _user_id: [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Disco Elysium")],
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service.compute_queue_fingerprint",
        lambda _entry_ids: "current-fingerprint",
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_for_fingerprint",
        lambda _db, _user_id, _fingerprint: current_pending,
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_overall",
        lambda _db, _user_id: current_pending,
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_overall_with_status",
        lambda _db, _user_id, status: previous_ready if status == "ready" else None,
    )

    state = get_queue_suggestion_state(user_id=1, db=db)

    assert state["suggestion"] is previous_ready
    assert state["is_stale"] is True
    assert state["is_generating"] is True
    assert state["can_generate"] is False
    assert "stay visible" in (state["detail"] or "")


def test_ensure_queue_suggestion_creates_pending_batch(monkeypatch):
    db = MagicMock()
    db.refresh.side_effect = lambda suggestion: setattr(suggestion, "id", 77)
    created_state = {
        "suggestion": SimpleNamespace(id=55, status="ready"),
        "is_stale": False,
        "is_generating": False,
        "can_generate": False,
        "can_adopt": False,
        "detail": "AI is generating a suggested play order.",
    }
    monkeypatch.setattr(
        "app.services.queue_suggestion_service.get_queue_suggestion_state",
        MagicMock(side_effect=[
            {"suggestion": None, "is_stale": False, "is_generating": False, "can_generate": True, "can_adopt": False, "detail": None},
            created_state,
        ]),
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._load_queue_rows",
        lambda _db, _user_id: [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Disco Elysium")],
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_for_fingerprint",
        lambda _db, _user_id, _fingerprint: None,
    )

    state, should_enqueue, suggestion_id = ensure_queue_suggestion(user_id=1, trigger_source="queue_tab", db=db)

    assert should_enqueue is True
    assert suggestion_id == 77
    assert state == created_state
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_ensure_queue_suggestion_creates_fresh_pending_batch_even_when_ready_exists(monkeypatch):
    db = MagicMock()
    db.refresh.side_effect = lambda suggestion: setattr(suggestion, "id", 91)
    matching_ready = SimpleNamespace(id=88, status="ready")
    created_state = {
        "suggestion": SimpleNamespace(id=91, status="pending"),
        "is_stale": False,
        "is_generating": True,
        "can_generate": False,
        "can_adopt": False,
        "detail": "AI is generating a suggested play order.",
    }
    monkeypatch.setattr(
        "app.services.queue_suggestion_service.get_queue_suggestion_state",
        MagicMock(side_effect=[
            {"suggestion": matching_ready, "is_stale": False, "is_generating": False, "can_generate": True, "can_adopt": True, "detail": None},
            created_state,
        ]),
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._load_queue_rows",
        lambda _db, _user_id: [_queue_row(1, 1, "Hades"), _queue_row(2, 2, "Disco Elysium")],
    )
    monkeypatch.setattr(
        "app.services.queue_suggestion_service._latest_for_fingerprint",
        lambda _db, _user_id, _fingerprint: matching_ready,
    )

    state, should_enqueue, suggestion_id = ensure_queue_suggestion(user_id=1, trigger_source="queue_tab", db=db)

    assert should_enqueue is True
    assert suggestion_id == 91
    assert state == created_state
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_adopt_queue_suggestion_reorders_queue(monkeypatch):
    db = MagicMock()
    queue_rows = [_queue_row(11, 1, "Hades"), _queue_row(22, 2, "Persona 5")]
    suggestion = SimpleNamespace(
        status="ready",
        items=[
            SimpleNamespace(entry_id=22, suggested_position=1),
            SimpleNamespace(entry_id=11, suggested_position=2),
        ],
    )
    monkeypatch.setattr("app.services.queue_suggestion_service._load_queue_rows", lambda _db, _user_id: queue_rows)
    monkeypatch.setattr("app.services.queue_suggestion_service._latest_for_fingerprint", lambda _db, _user_id, _fp: suggestion)
    reorder_mock = MagicMock(return_value={"total": 2, "entries": []})
    monkeypatch.setattr("app.services.queue_suggestion_service.play_queue_service.reorder", reorder_mock)

    result = adopt_queue_suggestion(user_id=1, db=db)

    assert result == {"total": 2, "entries": []}
    reorder_mock.assert_called_once()
