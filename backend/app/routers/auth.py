from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # TODO: Call user_service.create_user(db, user_in)
    # TODO: Raise HTTP 409 if email already registered
    raise NotImplementedError


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # TODO: Call auth_service.authenticate_user(db, form_data.username, form_data.password)
    # TODO: Raise HTTP 401 if credentials invalid or account inactive
    # TODO: Return auth_service.issue_tokens(user)
    raise NotImplementedError


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    # TODO: Decode refresh token, check it's not blacklisted in Redis
    # TODO: Issue a new access token (and optionally rotate the refresh token)
    raise NotImplementedError


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(refresh_token: str):
    # TODO: Call auth_service.revoke_refresh_token(refresh_token)
    #       — adds token to Redis blacklist with TTL matching its expiry
    raise NotImplementedError


# ---- Stretch goals ----

@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(email: str, db: Session = Depends(get_db)):
    # TODO (stretch): Generate a short-lived signed reset token
    # TODO (stretch): Send reset email via an email service (e.g. SendGrid, Resend)
    # Return 202 regardless of whether email exists (prevents enumeration)
    raise NotImplementedError


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(token: str, new_password: str, db: Session = Depends(get_db)):
    # TODO (stretch): Verify reset token signature and expiry
    # TODO (stretch): Hash new password and update user record
    # TODO (stretch): Invalidate token after use
    raise NotImplementedError
