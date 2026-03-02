from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.user import UserRole


def get_rate_limit_key(request):
    """
    Use authenticated user ID as the rate-limit key when available,
    falling back to IP address for unauthenticated requests.

    TODO: Extract the User from request.state (set it in a middleware or
          auth dependency) and return f"user:{user.id}"
    """
    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limit_key)


def get_rate_limit(role: UserRole) -> str:
    """Return the SlowAPI limit string for the given user role."""
    from app.config import settings  # local import to avoid circular dependency

    limits = {
        UserRole.BASIC:   settings.RATE_LIMIT_BASIC,
        UserRole.PREMIUM: settings.RATE_LIMIT_PREMIUM,
        UserRole.ADMIN:   settings.RATE_LIMIT_ADMIN,
    }
    return limits.get(role, settings.RATE_LIMIT_BASIC)
