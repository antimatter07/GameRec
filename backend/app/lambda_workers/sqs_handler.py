import json
import logging
from typing import Any

from app.services import task_queue
from app.workers.tasks.hltb_sync import run_enrich_game_hltb
from app.workers.tasks.rawg_sync import run_enrich_known_games, run_sync_recent_releases
from app.workers.tasks.recommendation import (
    run_generate_ai_explanations,
    run_generate_ai_picks,
    run_generate_queue_suggestion,
    run_precompute_for_user,
)

logger = logging.getLogger(__name__)


def _dispatch(task_name: str, payload: dict[str, Any]) -> None:
    if task_name == task_queue.TASK_PRECOMPUTE_FOR_USER:
        run_precompute_for_user(int(payload["user_id"]))
        return
    if task_name == task_queue.TASK_GENERATE_AI_EXPLANATIONS:
        run_generate_ai_explanations(int(payload["recommendation_id"]))
        return
    if task_name == task_queue.TASK_GENERATE_AI_PICKS:
        run_generate_ai_picks(int(payload["recommendation_id"]), int(payload["user_id"]))
        return
    if task_name == task_queue.TASK_GENERATE_QUEUE_SUGGESTION:
        run_generate_queue_suggestion(int(payload["suggestion_id"]), int(payload["user_id"]))
        return
    if task_name == task_queue.TASK_ENRICH_GAME_HLTB:
        run_enrich_game_hltb(int(payload["game_id"]))
        return
    if task_name == task_queue.TASK_RAWG_RECENT:
        run_sync_recent_releases(int(payload["max_requests"]), int(payload["days_back"]))
        return
    if task_name == task_queue.TASK_RAWG_ENRICH_KNOWN:
        run_enrich_known_games(int(payload["max_requests"]))
        return
    raise ValueError(f"Unknown task: {task_name}")


def handler(event, context):
    failures: list[dict[str, str]] = []
    for record in event.get("Records", []):
        message_id = record.get("messageId", "")
        try:
            body = json.loads(record["body"])
            task_name = body["task_name"]
            payload = body.get("payload") or {}
            logger.info("Running SQS task %s message_id=%s payload=%s", task_name, message_id, payload)
            _dispatch(task_name, payload)
        except Exception:
            logger.exception("SQS task failed message_id=%s", message_id)
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
