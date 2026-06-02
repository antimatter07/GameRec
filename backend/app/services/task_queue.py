import json
from typing import Any

from app.config import settings


TASK_PRECOMPUTE_FOR_USER = "recommendation.precompute_for_user"
TASK_GENERATE_AI_EXPLANATIONS = "recommendation.generate_ai_explanations"
TASK_GENERATE_AI_PICKS = "recommendation.generate_ai_picks"
TASK_GENERATE_QUEUE_SUGGESTION = "queue.generate_suggestion"
TASK_ENRICH_GAME_HLTB = "hltb_sync.enrich_game_hltb"
TASK_RAWG_RECENT = "rawg_sync.sync_recent_releases"
TASK_RAWG_ENRICH_KNOWN = "rawg_sync.enrich_known_games"


def _sqs_client():
    import boto3

    return boto3.client("sqs", region_name=settings.AWS_REGION)


def _send_sqs(queue_url: str, task_name: str, payload: dict[str, Any], delay_seconds: int = 0) -> str | None:
    if not queue_url:
        raise RuntimeError(f"Missing SQS queue URL for task {task_name}")
    response = _sqs_client().send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({"task_name": task_name, "payload": payload}),
        DelaySeconds=max(0, min(delay_seconds, 900)),
    )
    return response.get("MessageId")


def _enqueue(task_name: str, payload: dict[str, Any], queue_url: str, delay_seconds: int = 0) -> str | None:
    if settings.TASK_BACKEND == "sqs":
        return _send_sqs(queue_url, task_name, payload, delay_seconds)

    if task_name == TASK_PRECOMPUTE_FOR_USER:
        from app.workers.tasks.recommendation import precompute_for_user
        return precompute_for_user.delay(payload["user_id"]).id
    if task_name == TASK_GENERATE_AI_EXPLANATIONS:
        from app.workers.tasks.recommendation import generate_ai_explanations
        return generate_ai_explanations.delay(payload["recommendation_id"]).id
    if task_name == TASK_GENERATE_AI_PICKS:
        from app.workers.tasks.recommendation import generate_ai_picks
        return generate_ai_picks.delay(payload["recommendation_id"], payload["user_id"]).id
    if task_name == TASK_GENERATE_QUEUE_SUGGESTION:
        from app.workers.tasks.recommendation import generate_queue_suggestion
        return generate_queue_suggestion.delay(payload["suggestion_id"], payload["user_id"]).id
    if task_name == TASK_ENRICH_GAME_HLTB:
        from app.workers.tasks.hltb_sync import enrich_game_hltb
        return enrich_game_hltb.apply_async(args=[payload["game_id"]], countdown=delay_seconds).id
    if task_name == TASK_RAWG_RECENT:
        from app.workers.tasks.rawg_sync import sync_recent_releases
        return sync_recent_releases.delay(payload["max_requests"], payload["days_back"]).id
    if task_name == TASK_RAWG_ENRICH_KNOWN:
        from app.workers.tasks.rawg_sync import enrich_known_games
        return enrich_known_games.delay(payload["max_requests"]).id
    raise ValueError(f"Unknown task: {task_name}")


def enqueue_precompute_for_user(user_id: int) -> str | None:
    return _enqueue(
        TASK_PRECOMPUTE_FOR_USER,
        {"user_id": user_id},
        settings.SQS_RECOMMENDATION_QUEUE_URL,
    )


def enqueue_ai_explanations(recommendation_id: int) -> str | None:
    return _enqueue(
        TASK_GENERATE_AI_EXPLANATIONS,
        {"recommendation_id": recommendation_id},
        settings.SQS_AI_QUEUE_URL,
    )


def enqueue_ai_picks(recommendation_id: int, user_id: int) -> str | None:
    return _enqueue(
        TASK_GENERATE_AI_PICKS,
        {"recommendation_id": recommendation_id, "user_id": user_id},
        settings.SQS_AI_QUEUE_URL,
    )


def enqueue_queue_suggestion(suggestion_id: int, user_id: int) -> str | None:
    return _enqueue(
        TASK_GENERATE_QUEUE_SUGGESTION,
        {"suggestion_id": suggestion_id, "user_id": user_id},
        settings.SQS_AI_QUEUE_URL,
    )


def enqueue_hltb_game(game_id: int, delay_seconds: int = 0) -> str | None:
    return _enqueue(
        TASK_ENRICH_GAME_HLTB,
        {"game_id": game_id},
        settings.SQS_HLTB_QUEUE_URL,
        delay_seconds=delay_seconds,
    )


def enqueue_rawg_recent(max_requests: int, days_back: int) -> str | None:
    return _enqueue(
        TASK_RAWG_RECENT,
        {"max_requests": max_requests, "days_back": days_back},
        settings.SQS_RAWG_QUEUE_URL,
    )


def enqueue_rawg_enrich_known(max_requests: int) -> str | None:
    return _enqueue(
        TASK_RAWG_ENRICH_KNOWN,
        {"max_requests": max_requests},
        settings.SQS_RAWG_QUEUE_URL,
    )
