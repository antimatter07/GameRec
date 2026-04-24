from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import create_access_token, decode_access_token
from app.schemas.token import Token, GoogleLoginRequest
from app.schemas.user import UserCreate, UserOut
from app.services import auth_service, user_service

router = APIRouter()

DBDep = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: DBDep):
    return user_service.create_user(db, user_in)


@router.post("/login", response_model=Token)
def login(db: DBDep, form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: DBDep):
    if auth_service.is_refresh_token_blacklisted(refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    try:
        from app.config import settings
        import jwt
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Blacklist old refresh token and issue a fresh pair
    auth_service.revoke_refresh_token(refresh_token)
    return auth_service.issue_tokens(user)


@router.post("/google", response_model=Token)
def google_login(payload: GoogleLoginRequest, db: DBDep):
    try:
        return auth_service.login_with_google(db, payload.google_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(refresh_token: str):
    auth_service.revoke_refresh_token(refresh_token)


# ---- Stretch goals ----

@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(email: str, db: DBDep):
    # TODO (stretch): Generate a short-lived signed reset token
    # TODO (stretch): Send reset email via an email service (e.g. SendGrid, Resend)
    # Return 202 regardless of whether email exists (prevents enumeration)
    raise NotImplementedError


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(token: str, new_password: str, db: DBDep):
    # TODO (stretch): Verify reset token signature and expiry
    # TODO (stretch): Hash new password and update user record
    # TODO (stretch): Invalidate token after use
    raise NotImplementedError
