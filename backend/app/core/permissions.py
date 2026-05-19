from app.config import settings
from app.models.user import User, UserRole


def is_premium_or_admin(user: User) -> bool:
    return user.role in (UserRole.PREMIUM, UserRole.ADMIN)


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def can_access_ai_features(user: User) -> bool:
    """
    Gate for AI-enhanced recommendations and Game DNA.
    TODO: Extend to check subscription expiry, feature flags, A/B tests, etc.
    """
    return is_premium_or_admin(user)


def can_access_ai_picks(user: User) -> bool:
    """
    Gate for the LLM-native AI Picks surface.
    This is intentionally separate from the existing premium AI feature gate so
    the product can launch AI Picks to all users now and flip it to premium
    later through config only.
    """
    if not settings.AI_PICKS_REQUIRE_PREMIUM:
        return True
    return is_premium_or_admin(user)
