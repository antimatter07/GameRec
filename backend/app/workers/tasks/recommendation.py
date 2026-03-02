from app.workers.celery_app import celery_app


@celery_app.task(name="recommendation.precompute_for_user")
def precompute_for_user(user_id: int):
    """
    Asynchronously recompute recommendations for a user after their library changes.

    TODO: Create a DB session
    TODO: Fetch User by user_id
    TODO: Call recommendation_service.compute_recommendations(db, user)
    TODO: This task is dispatched by library endpoints after add/update/remove
    """
    raise NotImplementedError


@celery_app.task(name="recommendation.generate_ai_explanations")
def generate_ai_explanations(recommendation_id: int):
    """
    Populate LLM explanations for an existing Recommendation (premium users).

    TODO: Fetch Recommendation and its items from DB
    TODO: Call ai_service.generate_explanations(user, items)
    TODO: Persist explanation + confidence on each RecommendationItem
    TODO: This task is dispatched after compute_recommendations() for premium users
          so the initial response isn't blocked by LLM latency
    """
    raise NotImplementedError
