import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_precompute_for_user(user_id: int) -> None:
    """Run precompute for user.

    Recomputes a user recommendation batch and invalidates cached AI-derived taste summaries after library changes.

    Args:
        user_id: ID of the user whose background work should run.

    Returns:
        None."""
    from app.database import SessionLocal
    from app.services import recommendation_service

    db = SessionLocal()
    try:
        recommendation_service.compute_recommendations(user_id, db)
        logger.info("Precomputed recommendations for user %s", user_id)

        # Invalidate cached game-dna so it reflects the updated library
        try:
            from app.services import kv_store
            kv_store.delete(f"game_dna:{user_id}")
        except Exception:
            pass
        try:
            from app.services.ai_picks_service import invalidate_ai_picks_cache
            invalidate_ai_picks_cache(user_id)
        except Exception:
            pass
    except ValueError as exc:
        # User has no vectorised games yet — not an error worth retrying
        logger.warning("Could not precompute for user %s: %s", user_id, exc)
    except Exception:
        logger.exception("Failed to precompute recommendations for user %s", user_id)
        raise
    finally:
        db.close()


@celery_app.task(name="recommendation.precompute_for_user")
def precompute_for_user(user_id: int) -> None:
    """Precompute for user.

    Celery task entrypoint that delegates to the synchronous runner and lets Celery handle scheduling semantics.

    Args:
        user_id: ID of the user whose background work should run.

    Returns:
        None."""
    run_precompute_for_user(user_id)


def run_generate_ai_picks(recommendation_id: int, user_id: int) -> None:
    """Run generate AI picks.

    Generates an AI Picks recommendation batch and marks the row failed if generation cannot complete.

    Args:
        recommendation_id: ID of the recommendation batch to enrich or update.
        user_id: ID of the user whose background work should run.

    Returns:
        None."""
    from app.database import SessionLocal
    from app.models.recommendation import Recommendation, RecommendationKind, RecommendationStatus
    from app.services.ai_picks_service import generate_ai_picks_for_recommendation

    db = SessionLocal()
    try:
        generate_ai_picks_for_recommendation(recommendation_id, user_id, db)
        logger.info("Generated AI Picks batch %s for user %s", recommendation_id, user_id)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to generate AI Picks batch %s for user %s", recommendation_id, user_id)
        try:
            recommendation = (
                db.query(Recommendation)
                .filter(
                    Recommendation.id == recommendation_id,
                    Recommendation.user_id == user_id,
                    Recommendation.kind == RecommendationKind.AI_PICKS,
                )
                .first()
            )
            if recommendation is not None:
                recommendation.status = RecommendationStatus.FAILED
                recommendation.summary = str(exc)[:500]
                db.commit()
        except Exception:
            db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="recommendation.generate_ai_picks")
def generate_ai_picks(recommendation_id: int, user_id: int) -> None:
    """Generate ai picks.

    Celery task entrypoint that delegates to the synchronous runner and lets Celery handle scheduling semantics.

    Args:
        recommendation_id: ID of the recommendation batch to enrich or update.
        user_id: ID of the user whose background work should run.

    Returns:
        None."""
    run_generate_ai_picks(recommendation_id, user_id)


def run_generate_queue_suggestion(suggestion_id: int, user_id: int) -> None:
    """Run generate queue suggestion.

    Generates an AI queue ordering suggestion and stores failure metadata on the suggestion row when needed.

    Args:
        suggestion_id: ID of the queue suggestion row to generate.
        user_id: ID of the user whose background work should run.

    Returns:
        None."""
    from app.database import SessionLocal
    from app.models.queue_suggestion import QueueSuggestion
    from app.services.queue_suggestion_service import generate_queue_suggestion_for_user

    db = SessionLocal()
    try:
        generate_queue_suggestion_for_user(suggestion_id, user_id, db)
        logger.info("Generated queue suggestion %s for user %s", suggestion_id, user_id)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to generate queue suggestion %s for user %s", suggestion_id, user_id)
        try:
            suggestion = (
                db.query(QueueSuggestion)
                .filter(QueueSuggestion.id == suggestion_id, QueueSuggestion.user_id == user_id)
                .first()
            )
            if suggestion is not None:
                suggestion.status = "failed"
                suggestion.error_detail = str(exc)[:500]
                db.commit()
        except Exception:
            db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="queue.generate_suggestion")
def generate_queue_suggestion(suggestion_id: int, user_id: int) -> None:
    """Generate queue suggestion.

    Celery task entrypoint that delegates to the synchronous runner and lets Celery handle scheduling semantics.

    Args:
        suggestion_id: ID of the queue suggestion row to generate.
        user_id: ID of the user whose background work should run.

    Returns:
        None."""
    run_generate_queue_suggestion(suggestion_id, user_id)


def run_generate_ai_explanations(recommendation_id: int) -> None:
    """Run generate AI explanations.

    Loads a stored recommendation batch, generates premium explanations, and writes them onto recommendation items.

    Args:
        recommendation_id: ID of the recommendation batch to enrich or update.

    Returns:
        None."""
    from sqlalchemy.orm import joinedload

    from app.database import SessionLocal
    from app.models.recommendation import Recommendation, RecommendationItem
    from app.services import ai_service

    db = SessionLocal()
    try:
        recommendation: Recommendation | None = (
            db.query(Recommendation)
            .options(
                joinedload(Recommendation.items).joinedload(RecommendationItem.game)
            )
            .filter(Recommendation.id == recommendation_id)
            .first()
        )
        if recommendation is None:
            logger.warning("generate_ai_explanations: recommendation %s not found", recommendation_id)
            return

        items = sorted(recommendation.items, key=lambda i: i.rank)
        user  = recommendation.user

        explanations = ai_service.generate_explanations(user, items, db)

        for item, explanation in zip(items, explanations):
            if explanation:
                item.explanation = explanation

        db.commit()
        logger.info(
            "Generated AI explanations for recommendation %s (%d items)",
            recommendation_id,
            len(items),
        )
    except Exception:
        db.rollback()
        logger.exception("Failed to generate AI explanations for recommendation %s", recommendation_id)
        raise
    finally:
        db.close()


@celery_app.task(name="recommendation.generate_ai_explanations")
def generate_ai_explanations(recommendation_id: int) -> None:
    """Generate ai explanations.

    Celery task entrypoint that delegates to the synchronous runner and lets Celery handle scheduling semantics.

    Args:
        recommendation_id: ID of the recommendation batch to enrich or update.

    Returns:
        None."""
    run_generate_ai_explanations(recommendation_id)
