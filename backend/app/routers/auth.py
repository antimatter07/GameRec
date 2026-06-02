from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.token import GoogleLoginRequest
from app.schemas.user import UserCreate, UserOut
from app.services import auth_service, user_service

router = APIRouter()

DBDep = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: DBDep):
    """Register.

    Creates a new local user account and returns the public user representation.

    Args:
        user_in: Validated user registration payload.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        Serialized response object or task result produced by the operation."""
    return user_service.create_user(db, user_in)


@router.post("/login", response_model=UserOut)
def login(response: Response, db: DBDep, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login.

    Authenticates password credentials, issues an auth token, and writes session cookies.

    Args:
        response: FastAPI response object whose cookies should be updated.
        db: SQLAlchemy database session used to query or persist application data.
        form_data: OAuth2 form data containing login credentials. Defaults to Depends().

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        HTTPException: When the request cannot be authorized, validated, or completed."""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.issue_auth_token(user)
    auth_service.set_auth_cookie(response, token)
    auth_service.set_csrf_cookie(response, auth_service.generate_csrf_token())
    return user


@router.post("/google", response_model=UserOut)
def google_login(payload: GoogleLoginRequest, response: Response, db: DBDep):
    """Google login.

    Authenticates a Google identity token, links or creates a local account, and writes session cookies.

    Args:
        payload: Validated request payload or event payload for the operation.
        response: FastAPI response object whose cookies should be updated.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        HTTPException: When the request cannot be authorized, validated, or completed."""
    try:
        user = auth_service.login_with_google(db, payload.google_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    token = auth_service.issue_auth_token(user)
    auth_service.set_auth_cookie(response, token)
    auth_service.set_csrf_cookie(response, auth_service.generate_csrf_token())
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    auth_token: str | None = Cookie(default=None, alias=auth_service.AUTH_COOKIE_NAME),
):
    """Logout.

    Revokes the current auth token when present and clears the browser session cookie.

    Args:
        response: FastAPI response object whose cookies should be updated.
        auth_token: Authentication cookie token to revoke during logout.
            Defaults to Cookie(default=None, alias=auth_service.AUTH_COOKIE_NAME).

    Returns:
        Serialized response object or task result produced by the operation."""
    if auth_token:
        auth_service.revoke_auth_token(auth_token)
    auth_service.clear_auth_cookie(response)
    auth_service.set_csrf_cookie(response, auth_service.generate_csrf_token())


# ---- Stretch goals ----

@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(email: str, db: DBDep):
    # TODO (stretch): Generate a short-lived signed reset token
    # TODO (stretch): Send reset email via an email service (e.g. SendGrid, Resend)
    # Return 202 regardless of whether email exists (prevents enumeration)
    """Request password reset.

    Reserved endpoint for starting the future password reset workflow.

    Args:
        email: Email address associated with a password reset request.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        NotImplementedError: When the endpoint is a documented future implementation stub."""
    raise NotImplementedError


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(token: str, new_password: str, db: DBDep):
    # TODO (stretch): Verify reset token signature and expiry
    # TODO (stretch): Hash new password and update user record
    # TODO (stretch): Invalidate token after use
    """Confirm password reset.

    Reserved endpoint for completing the future password reset workflow.

    Args:
        token: Password reset token supplied by the caller.
        new_password: Replacement password submitted by the user.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        NotImplementedError: When the endpoint is a documented future implementation stub."""
    raise NotImplementedError
