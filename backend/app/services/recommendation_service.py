from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.models.user import User


def build_user_taste_profile(db: Session, user: User) -> dict:
    """
    Aggregate the user's rated library entries into a taste profile vector.

    TODO: Query all LibraryEntry rows for the user that have a rating
    TODO: For each game:
          - Load genre/tag list from Game model
          - Weight contribution by rating (e.g., rating/5.0)
    TODO: Multi-hot encode genres and tags (sum weighted vectors)
    TODO: Optionally run TF-IDF on game descriptions; consider storing
          pre-computed tf-idf vectors on the Game model to avoid recomputing
    TODO: Normalize the final vector (L2 norm)
    TODO: Cache the profile in Redis (key="taste:{user_id}") and invalidate
          whenever the user adds/updates a library entry
    """
    raise NotImplementedError


def compute_recommendations(db: Session, user: User, top_n: int = 10) -> Recommendation:
    """
    Content-based filtering via cosine similarity.

    TODO: Call build_user_taste_profile(db, user) to get the taste vector
    TODO: Load all Game records (or a candidate subset filtered by user's
          preferred genres) and their feature vectors
    TODO: Compute cosine similarity between taste vector and each game vector
    TODO: Exclude games already in the user's library
    TODO: Sort by similarity descending, take top_n
    TODO: Persist a Recommendation + RecommendationItem records
    TODO: For premium users, call ai_service.generate_explanations(user, items)
          — or dispatch it as a Celery task so the response isn't blocked
    """
    raise NotImplementedError


def get_or_generate(db: Session, user: User) -> Recommendation:
    """Return a recent cached recommendation or generate a fresh one."""
    # TODO: Look for a Recommendation generated within the last hour for this user
    # TODO: If found and not stale, return it
    # TODO: Otherwise call compute_recommendations(db, user)
    raise NotImplementedError
