import json
from unittest.mock import patch

from app.lambda_workers import sqs_handler
from app.services import task_queue


def _event(task_name: str, payload: dict):
    return {
        "Records": [
            {
                "messageId": "message-1",
                "body": json.dumps({"task_name": task_name, "payload": payload}),
            }
        ]
    }


def test_sqs_handler_dispatches_precompute_task():
    with patch("app.lambda_workers.sqs_handler.run_precompute_for_user") as run_precompute:
        result = sqs_handler.handler(
            _event(task_queue.TASK_PRECOMPUTE_FOR_USER, {"user_id": 123}),
            None,
        )

    run_precompute.assert_called_once_with(123)
    assert result == {"batchItemFailures": []}


def test_sqs_handler_reports_unknown_task_failure():
    result = sqs_handler.handler(_event("unknown.task", {}), None)

    assert result == {"batchItemFailures": [{"itemIdentifier": "message-1"}]}
