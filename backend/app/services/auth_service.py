import secrets
from datetime import datetime, timezone

import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.core.google_oauth import GoogleTokenError, verify_google_access_token
from app.core.redis_client import redis_client
from app.core.security import create_auth_token, decode_auth_token, verify_password
from app.models.auth_identity import AuthIdentity
from app.models.user import User, UserRole

AUTH_COOKIE_NAME = "auth_token"
AUTH_COOKIE_PATH = "/api"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_COOKIE_PATH = "/"
_AUTH_COOKIE_MAX_AGE_SECONDS = settings.SESSION_EXPIRE_DAYS * 86400
_REVOKED_TOKEN_PREFIX = "revoked_token:"


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, otherwise None."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        return None
    if not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def _revoked_token_key(jti: str) -> str:
    return f"{_REVOKED_TOKEN_PREFIX}{jti}"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def issue_auth_token(user: User) -> str:
    return create_auth_token(user.id, str(user.role))


def set_auth_cookie(response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=_AUTH_COOKIE_MAX_AGE_SECONDS,
        path=AUTH_COOKIE_PATH,
    )


def clear_auth_cookie(response) -> None:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path=AUTH_COOKIE_PATH,
        secure=settings.APP_ENV == "production",
        samesite="lax",
    )


def set_csrf_cookie(response, csrf_token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=_AUTH_COOKIE_MAX_AGE_SECONDS,
        path=CSRF_COOKIE_PATH,
    )


def clear_csrf_cookie(response) -> None:
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path=CSRF_COOKIE_PATH,
        secure=settings.APP_ENV == "production",
        samesite="lax",
    )


def revoke_auth_token(token: str) -> None:
    """Blacklist a JWT by jti until its natural expiry so logout invalidates it."""
    try:
        payload = decode_auth_token(token)
    except Exception:
        return

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return

    ttl = max(1, int(exp) - int(datetime.now(timezone.utc).timestamp()))
    redis_client.setex(_revoked_token_key(jti), ttl, "1")


def is_auth_token_revoked(payload: dict) -> bool:
    jti = payload.get("jti")
    if not jti:
        return True
    return redis_client.exists(_revoked_token_key(jti)) == 1


def get_user_for_token(db: Session, token: str) -> User | None:
    try:
        payload = decode_auth_token(token)
    except Exception:
        return None

    if is_auth_token_revoked(payload):
        return None

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        return None
    return user


def _derive_display_name(db: Session, email: str) -> str:
    """Derive a unique display_name from the email local-part, appending a counter on collision."""
    base = email.split("@", 1)[0][:90] or "user"
    candidate, n = base, 1
    while db.query(User).filter(User.display_name == candidate).first():
        n += 1
        candidate = f"{base}{n}"
    return candidate


def login_with_google(db: Session, id_token_str: str) -> User:
    """Verify a Google access token and return the matching local user."""
    try:
        claims = verify_google_access_token(id_token_str)
    except GoogleTokenError as exc:
        raise ValueError(str(exc))

    sub = claims["sub"]
    email = claims["email"].lower()
    name = claims.get("name")
    pic = claims.get("picture")

    identity = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == "google", AuthIdentity.provider_sub == sub)
        .first()
    )
    if identity:
        user = identity.user
    else:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                hashed_password=None,
                display_name=name or _derive_display_name(db, email),
                avatar_url=pic,
                role=UserRole.BASIC,
                is_active=True,
            )
            db.add(user)
            db.flush()

        db.add(
            AuthIdentity(
                user_id=user.id,
                provider="google",
                provider_sub=sub,
                email_at_link=email,
            )
        )
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise ValueError("This account has been disabled")

    return user
