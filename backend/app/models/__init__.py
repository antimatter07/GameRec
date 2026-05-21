# Import all models here so Alembic's env.py can discover them via Base.metadata
from app.models.user import User, UserRole
from app.models.auth_identity import AuthIdentity
from app.models.game import Game
from app.models.game_external_id import GameExternalId
from app.models.library import LibraryEntry, LibraryStatus
from app.models.recommendation import Recommendation, RecommendationItem, RecommendationFeedback
from app.models.play_queue import PlayQueueEntry
from app.models.queue_suggestion import QueueSuggestion, QueueSuggestionItem
from app.models.journal import SessionLog
from app.models.rawg_sync_state import RawgSeenGame, RawgSyncState

__all__ = [
    "User",
    "UserRole",
    "AuthIdentity",
    "Game",
    "GameExternalId",
    "LibraryEntry",
    "LibraryStatus",
    "Recommendation",
    "RecommendationItem",
    "RecommendationFeedback",
    "PlayQueueEntry",
    "QueueSuggestion",
    "QueueSuggestionItem",
    "SessionLog",
    "RawgSyncState",
    "RawgSeenGame",
]
