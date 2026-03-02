from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, otherwise None."""
    # TODO: db.query(User).filter(User.email == email).first()
    # TODO: Return None if user not found or not active
    # TODO: Return None if not verify_password(password, user.hashed_password)
    raise NotImplementedError


def issue_tokens(user: User) -> dict:
    """Create and return a fresh access + refresh token pair."""
    # TODO: access_token  = create_access_token(user.id, user.role)
    # TODO: refresh_token = create_refresh_token(user.id)
    # TODO: Store refresh_token in Redis (key="refresh:{user_id}", value=token, ttl=REFRESH_TOKEN_EXPIRE_DAYS*86400)
    #       This allows single-session enforcement; use a set if you want multi-device support
    raise NotImplementedError


def revoke_refresh_token(token: str) -> None:
    """Add a refresh token to the Redis blacklist so it cannot be reused."""
    # TODO: Decode token to get expiry (or use a fixed TTL)
    # TODO: redis_client.setex(f"blacklist:{token}", ttl, "1")
    raise NotImplementedError
