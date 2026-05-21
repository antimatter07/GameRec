from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.library import LibraryStatus
from app.schemas.play_queue import PlayQueueEnqueue
from app.services import play_queue_service


def _query(first_value=None, scalar_value=0):
    query = MagicMock()
    query.filter.return_value = query
    query.first.return_value = first_value
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
