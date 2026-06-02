"""
Celery tasks for enriching games with HowLongToBeat playtime data.

Tasks:
  enrich_game_hltb(game_id)  — enrich a single game
  enrich_all_hltb()          — enqueue tasks for all un-enriched games
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.game import Game
from app.services import task_queue
from app.utils.hltb_client import fetch_hltb
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_enrich_game_hltb(game_id: int) -> None:
    """Run enrich game hltb.

    Fetches HLTB playtime data for one game, stores any confident match, and stamps the sync timestamp either way.

    Args:
        game_id: Application game ID to enrich.

    Returns:
        None."""
    db = SessionLocal()
    try:
        game = db.get(Game, game_id)
        if game is None:
            logger.warning("enrich_game_hltb: game_id=%d not found", game_id)
            return

        result = asyncio.run(fetch_hltb(game.name))

        if result is not None:
            game.hltb_main_hours          = result["main"]
            game.hltb_main_extra_hours    = result["main_extra"]
            game.hltb_completionist_hours = result["completionist"]
            logger.info(
                "HLTB enriched game_id=%d (%r): main=%.1fh",
                game_id, game.name, result["main"] or 0,
            )
        else:
            logger.debug("HLTB: no confident match for game_id=%d (%r)", game_id, game.name)

        # Always stamp hltb_synced_at so we don't retry on every enrich_all_hltb run.
        game.hltb_synced_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        db.rollback()
        logger.exception("enrich_game_hltb failed for game_id=%d: %s", game_id, exc)
        raise
    finally:
        db.close()


@celery_app.task(name="hltb_sync.enrich_game_hltb", bind=True, max_retries=3)
def enrich_game_hltb(self, game_id: int):
    """Enrich game hltb.

    Celery task entrypoint that delegates to the synchronous runner and retries
    transient HLTB or database failures.

    Args:
        game_id: Application game ID to enrich.

    Returns:
        Task result returned by the delegated runner, if any.

    Raises:
        Exception: When Celery schedules a retry for the failed enrichment run."""
    try:
        run_enrich_game_hltb(game_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="hltb_sync.enrich_all_hltb")
def enrich_all_hltb() -> int:
    """Enrich all hltb.

    Finds games without HLTB sync timestamps and enqueues staggered enrichment jobs for them.

    Returns:
        Integer value produced by the operation."""
    db = SessionLocal()
    try:
        game_ids = (
            db.query(Game.id)
            .filter(Game.hltb_synced_at.is_(None))
            .order_by(Game.id)
            .all()
        )
    finally:
        db.close()

    ids = [row[0] for row in game_ids]
    for i, game_id in enumerate(ids):
        task_queue.enqueue_hltb_game(game_id, delay_seconds=i * 2)

    logger.info("enrich_all_hltb: enqueued %d games", len(ids))
    return len(ids)
