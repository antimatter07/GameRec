import secrets
from datetime import datetime, timezone

import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.core.google_oauth import GoogleTokenError, verify_google_access_token
from app.core.security import create_auth_token, decode_auth_token, verify_password
from app.models.auth_identity import AuthIdentity
from app.models.user import User, UserRole
from app.services import kv_store

AUTH_COOKIE_NAME = "auth_token"
AUTH_COOKIE_PATH = "/api"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_COOKIE_PATH = "/"
_AUTH_COOKIE_MAX_AGE_SECONDS = settings.SESSION_EXPIRE_DAYS * 86400
_REVOKED_TOKEN_PREFIX = "revoked_token:"


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate user.

    Performs the service operation behind a stable module-level interface.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        email: Email address used to identify the user account.
        password: Plain-text password supplied during authentication.

    Returns:
        User | None when a matching value is available; otherwise None."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        return None
    if not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def _revoked_token_key(jti: str) -> str:
    """Revoked token key.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        jti: JWT ID claim used to identify a revoked token.

    Returns:
        String value produced by the operation."""
    return f"{_REVOKED_TOKEN_PREFIX}{jti}"


def generate_csrf_token() -> str:
    """Generate csrf token.

    Produces AI-backed content and validates it before storage or return.

    Returns:
        String value produced by the operation."""
    return secrets.token_urlsafe(32)


def issue_auth_token(user: User) -> str:
    """Issue auth token.

    Performs the service operation behind a stable module-level interface.

    Args:
        user: Authenticated user model associated with the operation.

    Returns:
        String value produced by the operation."""
    return create_auth_token(user.id, str(user.role))


def set_auth_cookie(response, token: str) -> None:
    """Set auth cookie.

    Updates response or storage state while keeping cookie and cache settings centralized.

    Args:
        response: FastAPI response object whose cookies should be updated.
        token: JWT or opaque token value to validate, revoke, or store.

    Returns:
        None."""
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite=settings.COOKIE_SAMESITE,
        max_age=_AUTH_COOKIE_MAX_AGE_SECONDS,
        path=AUTH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN or None,
    )


def clear_auth_cookie(response) -> None:
    """Clear auth cookie.

    Updates response or storage state while keeping cookie and cache settings centralized.

    Args:
        response: FastAPI response object whose cookies should be updated.

    Returns:
        None."""
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path=AUTH_COOKIE_PATH,
        secure=settings.APP_ENV == "production",
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN or None,
    )


def set_csrf_cookie(response, csrf_token: str) -> None:
    """Set csrf cookie.

    Updates response or storage state while keeping cookie and cache settings centralized.

    Args:
        response: FastAPI response object whose cookies should be updated.
        csrf_token: CSRF token value to write into the response cookie.

    Returns:
        None."""
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.APP_ENV == "production",
        samesite=settings.COOKIE_SAMESITE,
        max_age=_AUTH_COOKIE_MAX_AGE_SECONDS,
        path=CSRF_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN or None,
    )


def clear_csrf_cookie(response) -> None:
    """Clear csrf cookie.

    Updates response or storage state while keeping cookie and cache settings centralized.

    Args:
        response: FastAPI response object whose cookies should be updated.

    Returns:
        None."""
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path=CSRF_COOKIE_PATH,
        secure=settings.APP_ENV == "production",
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN or None,
    )


def revoke_auth_token(token: str) -> None:
    """Revoke auth token.

    Performs the service operation behind a stable module-level interface.

    Args:
        token: JWT or opaque token value to validate, revoke, or store.

    Returns:
        None."""
    try:
        payload = decode_auth_token(token)
    except Exception:
        return

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return

    ttl = max(1, int(exp) - int(datetime.now(timezone.utc).timestamp()))
    kv_store.set_text(_revoked_token_key(jti), "1", ttl_seconds=ttl)


def is_auth_token_revoked(payload: dict) -> bool:
    """Check auth token revoked.

    Evaluates service rules and returns a boolean or reason code without mutating application state.

    Args:
        payload: Validated input payload for the operation.

    Returns:
        True when the condition is met; otherwise False."""
    jti = payload.get("jti")
    if not jti:
        return True
    return kv_store.exists(_revoked_token_key(jti))


def get_user_for_token(db: Session, token: str) -> User | None:
    """Get user for token.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        token: JWT or opaque token value to validate, revoke, or store.

    Returns:
        User | None when a matching value is available; otherwise None."""
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
    """Derive display name.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        email: Email address used to identify the user account.

    Returns:
        String value produced by the operation."""
    base = email.split("@", 1)[0][:90] or "user"
    candidate, n = base, 1
    while db.query(User).filter(User.display_name == candidate).first():
        n += 1
        candidate = f"{base}{n}"
    return candidate


def login_with_google(db: Session, id_token_str: str) -> User:
    """Log in with google.

    Performs the service operation behind a stable module-level interface.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        id_token_str: Google identity token string returned by the OAuth flow.

    Returns:
        User produced by the operation.

    Raises:
        ValueError: When supplied input cannot be validated or mapped to application data."""
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
