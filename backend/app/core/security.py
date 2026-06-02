from datetime import datetime, timedelta, timezone
import secrets

from fastapi import HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
import bcrypt

from app.config import settings


def hash_password(plain: str) -> str:
    """Hash a plain-text password.

    Uses bcrypt to produce a salted password hash suitable for storage.

    Args:
        plain: Plain-text password to hash.

    Returns:
        Bcrypt password hash string."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password.

    Compares a supplied password against a stored bcrypt hash.

    Args:
        plain: Plain-text password supplied by the user.
        hashed: Stored bcrypt password hash.

    Returns:
        True when the password matches the stored hash; otherwise False."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_auth_token(user_id: int, role: str) -> str:
    """Create an auth token.

    Builds a signed session JWT containing the user ID, role, expiry, token type, and unique token ID.

    Args:
        user_id: ID of the authenticated user.
        role: Role value embedded in the token claims.

    Returns:
        Encoded JWT string."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.SESSION_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "auth",
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_auth_token(token: str) -> dict:
    """Decode an auth token.

    Validates the JWT signature, algorithm, expiry, and auth token type before returning claims.

    Args:
        token: Encoded JWT string to validate.

    Returns:
        Decoded JWT claims dictionary.

    Raises:
        HTTPException: When the token is invalid, expired, or has the wrong token type."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "auth":
            raise InvalidTokenError("Wrong token type")
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
