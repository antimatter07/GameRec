from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import can_access_ai_picks
from app.database import get_db
from app.models.user import User, UserRole
from app.services import auth_service


def get_current_user(
    auth_cookie: str | None = Cookie(default=None, alias=auth_service.AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the JWT auth cookie."""
    if not auth_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = auth_service.get_user_for_token(db, auth_cookie)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user


def require_role(*roles: UserRole):
    """Dependency factory — restricts an endpoint to the given roles."""
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return _check


# Convenience guards — import these in routers
require_basic   = require_role(UserRole.BASIC, UserRole.PREMIUM, UserRole.ADMIN)
require_premium = require_role(UserRole.PREMIUM, UserRole.ADMIN)
require_admin   = require_role(UserRole.ADMIN)


def require_ai_picks(current_user: User = Depends(require_basic)) -> User:
    if not can_access_ai_picks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI Picks is not available for your account",
        )
    return current_user
