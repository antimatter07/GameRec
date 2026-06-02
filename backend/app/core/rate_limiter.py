from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.user import UserRole


def get_rate_limit_key(request):
    """Get rate limit key.

    Returns the request IP address currently used by SlowAPI to bucket rate-limited callers.

    Args:
        request: Incoming FastAPI request object.

    Returns:
        Rate-limit key string."""
    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limit_key)


def get_rate_limit(role: UserRole) -> str:
    """Get rate limit.

    Maps a user role to the configured SlowAPI rate-limit string.

    Args:
        role: User role whose request limit should be selected.

    Returns:
        SlowAPI-compatible limit string."""
    from app.config import settings  # local import to avoid circular dependency

    limits = {
        UserRole.BASIC:   settings.RATE_LIMIT_BASIC,
        UserRole.PREMIUM: settings.RATE_LIMIT_PREMIUM,
        UserRole.ADMIN:   settings.RATE_LIMIT_ADMIN,
    }
    return limits.get(role, settings.RATE_LIMIT_BASIC)
