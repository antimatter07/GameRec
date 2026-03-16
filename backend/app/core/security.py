from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
import bcrypt

from app.config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire, "type": "access"}
    # TODO: return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    raise NotImplementedError


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    # TODO: Consider adding a "jti" (JWT ID) claim for fine-grained per-token revocation
    # TODO: return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    raise NotImplementedError


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token. Raises HTTP 401 on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise InvalidTokenError("Wrong token type")
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
