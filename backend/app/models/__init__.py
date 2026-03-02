# Import all models here so Alembic's env.py can discover them via Base.metadata
from app.models.user import User, UserRole
from app.models.game import Game
from app.models.library import LibraryEntry, LibraryStatus
from app.models.recommendation import Recommendation, RecommendationItem, RecommendationFeedback

__all__ = [
    "User",
    "UserRole",
    "Game",
    "LibraryEntry",
    "LibraryStatus",
    "Recommendation",
    "RecommendationItem",
    "RecommendationFeedback",
]
