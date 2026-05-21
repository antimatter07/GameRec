from app.config import settings
from app.models.user import User, UserRole


def is_premium_or_admin(user: User) -> bool:
    """Return whether the user is allowed to use premium-tier features."""
    return user.role in (UserRole.PREMIUM, UserRole.ADMIN)


def is_admin(user: User) -> bool:
    """Return whether the user has admin privileges."""
    return user.role == UserRole.ADMIN


def can_access_ai_features(user: User) -> bool:
    """
    Gate for premium AI-enhanced recommendations and Game DNA.

    TODO: Extend to check subscription expiry, feature flags, A/B tests, etc.
    """
    return is_premium_or_admin(user)


def can_access_ai_picks(user: User) -> bool:
    """
    Gate for the LLM-native AI Picks surface.

    This gate is intentionally separate from the premium AI feature gate so
    the product can be enabled for everyone or restricted later through
    configuration without changing the route layer.
    """
    if not settings.AI_PICKS_REQUIRE_PREMIUM:
        return True
    return is_premium_or_admin(user)


def can_access_queue_suggestions(user: User) -> bool:
    """
    Gate for AI suggested play-order access.

    This is kept separate from AI Picks so launch access can differ and the
    feature can later become premium-only through configuration alone.
    """
    if not settings.QUEUE_SUGGESTION_REQUIRE_PREMIUM:
        return True
    return is_premium_or_admin(user)
