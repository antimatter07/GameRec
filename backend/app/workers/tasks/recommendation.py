import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="recommendation.precompute_for_user")
def precompute_for_user(user_id: int) -> None:
    """
    Asynchronously recompute recommendations for a user after their library changes.
    Dispatched by library endpoints (add / update / remove).
    """
    from app.database import SessionLocal
    from app.services import recommendation_service

    db = SessionLocal()
    try:
        recommendation_service.compute_recommendations(user_id, db)
        logger.info("Precomputed recommendations for user %s", user_id)

        # Invalidate cached game-dna so it reflects the updated library
        try:
            import redis as redis_lib
            from app.config import settings
            r = redis_lib.from_url(settings.REDIS_URL)
            r.delete(f"game_dna:{user_id}")
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


@celery_app.task(name="recommendation.generate_ai_picks")
def generate_ai_picks(recommendation_id: int, user_id: int) -> None:
    """
    Build an LLM-native AI Picks batch for the given user and recommendation row.
    """
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


@celery_app.task(name="recommendation.generate_ai_explanations")
def generate_ai_explanations(recommendation_id: int) -> None:
    """
    Populate LLM explanations for an existing Recommendation (premium users).
    Dispatched after compute_recommendations() so the HTTP response is not blocked.
    """
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
