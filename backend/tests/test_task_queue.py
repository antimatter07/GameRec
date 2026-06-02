import json
from unittest.mock import MagicMock

from app.config import settings
from app.services import task_queue


def test_enqueue_ai_picks_sends_sqs_message(monkeypatch):
    monkeypatch.setattr(settings, "TASK_BACKEND", "sqs")
    monkeypatch.setattr(settings, "AWS_REGION", "ap-southeast-1")
    monkeypatch.setattr(settings, "SQS_AI_QUEUE_URL", "https://sqs.example/ai")
    mock_sqs = MagicMock()
    mock_sqs.send_message.return_value = {"MessageId": "msg-1"}
    monkeypatch.setattr(task_queue, "_sqs_client", lambda: mock_sqs)

    message_id = task_queue.enqueue_ai_picks(10, 20)

    assert message_id == "msg-1"
    kwargs = mock_sqs.send_message.call_args.kwargs
    assert kwargs["QueueUrl"] == "https://sqs.example/ai"
    assert json.loads(kwargs["MessageBody"]) == {
        "task_name": task_queue.TASK_GENERATE_AI_PICKS,
        "payload": {"recommendation_id": 10, "user_id": 20},
    }


def test_enqueue_hltb_caps_sqs_delay(monkeypatch):
    monkeypatch.setattr(settings, "TASK_BACKEND", "sqs")
    monkeypatch.setattr(settings, "SQS_HLTB_QUEUE_URL", "https://sqs.example/hltb")
    mock_sqs = MagicMock()
    mock_sqs.send_message.return_value = {"MessageId": "msg-2"}
    monkeypatch.setattr(task_queue, "_sqs_client", lambda: mock_sqs)

    task_queue.enqueue_hltb_game(42, delay_seconds=9999)

    assert mock_sqs.send_message.call_args.kwargs["DelaySeconds"] == 900
