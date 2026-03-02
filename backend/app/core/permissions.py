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
