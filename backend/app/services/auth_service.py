from datetime import datetime, timezone

import jwt

from sqlalchemy.orm import Session

from app.config import settings
from app.core.redis_client import redis_client
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, otherwise None."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_tokens(user: User) -> dict:
    """Create and return a fresh access + refresh token pair."""
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    redis_client.setex(f"refresh:{user.id}", ttl, refresh_token)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def revoke_refresh_token(token: str) -> None:
    """Add a refresh token to the Redis blacklist so it cannot be reused."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp = payload.get("exp", 0)
        ttl = max(1, exp - int(datetime.now(timezone.utc).timestamp()))
        redis_client.setex(f"blacklist:{token}", ttl, "1")
    except Exception:
        pass  # Already expired or invalid — no need to blacklist


def is_refresh_token_blacklisted(token: str) -> bool:
    return redis_client.exists(f"blacklist:{token}") == 1
