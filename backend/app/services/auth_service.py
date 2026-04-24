from datetime import datetime, timezone

import jwt

from sqlalchemy.orm import Session

from app.config import settings
from app.core.redis_client import redis_client
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.google_oauth import verify_google_id_token, GoogleTokenError
from app.models.auth_identity import AuthIdentity
from app.models.user import User, UserRole


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


def _derive_display_name(db: Session, email: str) -> str:
    """Derive a unique display_name from the email local-part, appending a counter on collision."""
    base = email.split("@", 1)[0][:90] or "user"
    candidate, n = base, 1
    while db.query(User).filter(User.display_name == candidate).first():
        n += 1
        candidate = f"{base}{n}"
    return candidate


def login_with_google(db: Session, id_token_str: str) -> dict:
    """
    Verify a Google ID token and return our own JWT pair.
    Lookup order: (provider, sub) exact hit → verified-email match → new user.
    After this call the session is 100% our JWT flow; Google is not consulted again.
    """
    try:
        claims = verify_google_id_token(id_token_str)
    except GoogleTokenError as e:
        raise ValueError(str(e))

    sub   = claims["sub"]
    email = claims["email"].lower()
    name  = claims.get("name")
    pic   = claims.get("picture")

    # 1. Exact identity hit (returning Google user)
    identity = (
        db.query(AuthIdentity)
          .filter(AuthIdentity.provider == "google", AuthIdentity.provider_sub == sub)
          .first()
    )
    if identity:
        user = identity.user
    else:
        # 2. Verified-email match → link Google to an existing password account
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            # 3. Brand-new user — auto-register as BASIC
            user = User(
                email=email,
                hashed_password=None,
                display_name=name or _derive_display_name(db, email),
                avatar_url=pic,
                role=UserRole.BASIC,
                is_active=True,
            )
            db.add(user)
            db.flush()  # assign user.id before creating the identity row

        db.add(AuthIdentity(
            user_id=user.id,
            provider="google",
            provider_sub=sub,
            email_at_link=email,
        ))
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise ValueError("This account has been disabled")

    return issue_tokens(user)
