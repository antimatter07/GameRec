from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the JWT and return the authenticated User, or raise 401."""
    # TODO: Call decode_access_token(token) to get payload
    # TODO: Query db for User by payload["sub"] (user ID)
    # TODO: Raise HTTP 401 if token invalid, expired, or user not found / inactive
    raise NotImplementedError


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
