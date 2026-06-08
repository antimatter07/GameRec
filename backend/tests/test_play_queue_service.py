from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.library import LibraryStatus
from app.schemas.play_queue import PlayQueueEnqueue, PlayQueueReorder
from app.services import play_queue_service


def _query(first_value=None, scalar_value=0):
    query = MagicMock()
    query.filter.return_value = query
    query.first.return_value = first_value
    query.options.return_value = query
    query.with_entities.return_value = query
    query.scalar.return_value = scalar_value
    return query


@pytest.mark.parametrize(
    "status",
    [
        LibraryStatus.PLAYING,
        LibraryStatus.COMPLETED,
        LibraryStatus.DROPPED,
        LibraryStatus.WISHLIST,
    ],
)
def test_enqueue_rejects_non_queueable_statuses(status):
    db = MagicMock()
    db.query.return_value = _query(SimpleNamespace(id=10, user_id=1, status=status))

    with pytest.raises(HTTPException) as exc:
        play_queue_service.enqueue(db, 1, PlayQueueEnqueue(entry_id=10))

    assert exc.value.status_code == 422


@pytest.mark.parametrize("status", [LibraryStatus.BACKLOG, LibraryStatus.REPLAYING])
def test_enqueue_accepts_backlog_and_replaying(monkeypatch, status):
    db = MagicMock()
    db.query.side_effect = [
        _query(SimpleNamespace(id=10, user_id=1, status=status)),
        _query(None),
        _query(scalar_value=8),
    ]
    monkeypatch.setattr(play_queue_service, "_load_queue", lambda _db, _user_id: [])

    result = play_queue_service.enqueue(db, 1, PlayQueueEnqueue(entry_id=10))

    assert result == {"total": 0, "entries": []}
    queue_entry = db.add.call_args.args[0]
    assert queue_entry.position == 9
    db.commit.assert_called_once()
    assert db.method_calls[0][0] == "execute"


def test_enqueue_uses_max_position_not_count_for_gapped_queue(monkeypatch):
    db = MagicMock()
    db.query.side_effect = [
        _query(SimpleNamespace(id=10, user_id=1, status=LibraryStatus.BACKLOG)),
        _query(None),
        _query(scalar_value=9),
    ]
    monkeypatch.setattr(play_queue_service, "_load_queue", lambda _db, _user_id: [])

    play_queue_service.enqueue(db, 1, PlayQueueEnqueue(entry_id=10))

    queue_entry = db.add.call_args.args[0]
    assert queue_entry.position == 10


def test_enqueue_retries_integrity_error_once(monkeypatch):
    db = MagicMock()
    db.query.side_effect = [
        _query(SimpleNamespace(id=10, user_id=1, status=LibraryStatus.BACKLOG)),
        _query(None),
        _query(scalar_value=8),
        _query(SimpleNamespace(id=10, user_id=1, status=LibraryStatus.BACKLOG)),
        _query(None),
        _query(scalar_value=8),
    ]
    db.commit.side_effect = [IntegrityError("insert", {}, Exception("duplicate position")), None]
    monkeypatch.setattr(play_queue_service, "_load_queue", lambda _db, _user_id: [])

    result = play_queue_service.enqueue(db, 1, PlayQueueEnqueue(entry_id=10))

    assert result == {"total": 0, "entries": []}
    assert db.rollback.call_count == 1
    assert db.commit.call_count == 2


def test_enqueue_returns_conflict_after_repeated_integrity_errors(monkeypatch):
    db = MagicMock()
    db.query.side_effect = [
        _query(SimpleNamespace(id=10, user_id=1, status=LibraryStatus.BACKLOG)),
        _query(None),
        _query(scalar_value=8),
        _query(SimpleNamespace(id=10, user_id=1, status=LibraryStatus.BACKLOG)),
        _query(None),
        _query(scalar_value=8),
        _query(SimpleNamespace(id=10, user_id=1, status=LibraryStatus.BACKLOG)),
        _query(None),
        _query(scalar_value=8),
    ]
    db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate position"))
    monkeypatch.setattr(play_queue_service, "_load_queue", lambda _db, _user_id: [])

    with pytest.raises(HTTPException) as exc:
        play_queue_service.enqueue(db, 1, PlayQueueEnqueue(entry_id=10))

    assert exc.value.status_code == 409
    assert exc.value.detail == "Queue changed while processing; please retry."
    assert db.rollback.call_count == 3


def test_dequeue_acquires_queue_lock():
    queue_entry = SimpleNamespace(position=2)
    db = MagicMock()
    db.query.return_value = _query(queue_entry)

    play_queue_service.dequeue(db, 1, 10)

    assert db.method_calls[0][0] == "execute"
    db.delete.assert_called_once_with(queue_entry)
    db.commit.assert_called_once()


def test_reorder_acquires_queue_lock(monkeypatch):
    rows = [
        SimpleNamespace(entry_id=10, position=1),
        SimpleNamespace(entry_id=20, position=2),
    ]
    query = _query()
    query.all.return_value = rows
    db = MagicMock()
    db.query.return_value = query
    monkeypatch.setattr(play_queue_service, "_load_queue", lambda _db, _user_id: [])

    result = play_queue_service.reorder(db, 1, PlayQueueReorder(ordered_entry_ids=[20, 10]))

    assert result == {"total": 0, "entries": []}
    assert db.method_calls[0][0] == "execute"
    assert [row.position for row in rows] == [2, 1]
    db.commit.assert_called_once()


def test_remove_entry_from_queue_acquires_queue_lock():
    queue_entry = SimpleNamespace(position=2)
    db = MagicMock()
    db.query.side_effect = [_query(queue_entry), _query(None)]

    result = play_queue_service.remove_entry_from_queue(db, 1, 10)

    assert result == {"queue_removed": True, "next_game_candidate": None}
    assert db.method_calls[0][0] == "execute"
    db.delete.assert_called_once_with(queue_entry)
    db.commit.assert_not_called()
