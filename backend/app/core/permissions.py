from app.config import settings
from app.models.user import User, UserRole


def is_premium_or_admin(user: User) -> bool:
    """Check premium or admin access.

    Returns whether the user has a premium-capable role.

    Args:
        user: User model whose role should be checked.

    Returns:
        True when the user is premium or admin; otherwise False."""
    return user.role in (UserRole.PREMIUM, UserRole.ADMIN)


def is_admin(user: User) -> bool:
    """Check admin access.

    Returns whether the user has the admin role.

    Args:
        user: User model whose role should be checked.

    Returns:
        True when the user is an admin; otherwise False."""
    return user.role == UserRole.ADMIN


def can_access_ai_features(user: User) -> bool:
    """Check AI feature access.

    Central feature gate for premium AI recommendations and Game DNA.

    Args:
        user: User model whose feature access should be checked.

    Returns:
        True when the user can access premium AI features; otherwise False."""
    return is_premium_or_admin(user)


def can_access_ai_picks(user: User) -> bool:
    """Check AI Picks access.

    Applies the AI Picks premium setting before falling back to role-based access.

    Args:
        user: User model whose feature access should be checked.

    Returns:
        True when the user can access AI Picks; otherwise False."""
    if not settings.AI_PICKS_REQUIRE_PREMIUM:
        return True
    return is_premium_or_admin(user)


def can_access_queue_suggestions(user: User) -> bool:
    """Check queue suggestion access.

    Applies the queue suggestion premium setting before falling back to role-based access.

    Args:
        user: User model whose feature access should be checked.

    Returns:
        True when the user can access AI queue suggestions; otherwise False."""
    if not settings.QUEUE_SUGGESTION_REQUIRE_PREMIUM:
        return True
    return is_premium_or_admin(user)
