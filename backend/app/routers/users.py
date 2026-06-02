from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_basic
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.services import user_service

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Get me.

    Returns the authenticated user profile.

    Args:
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(get_current_user).

    Returns:
        Serialized response object or task result produced by the operation."""
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update me.

    Updates the authenticated user profile.

    Args:
        updates: Validated update payload containing changed fields.
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(get_current_user).

    Returns:
        Serialized response object or task result produced by the operation."""
    return user_service.update_user(db, current_user, updates)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete me.

    Deletes the authenticated user account.

    Args:
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(get_current_user).

    Returns:
        None."""
    user_service.delete_user(db, current_user)


@router.post("/me/request-premium", status_code=status.HTTP_202_ACCEPTED)
def request_premium(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Create a PremiumRequest record in the DB (model not yet created)
    # TODO: Optionally notify admin via email or in-app notification
    # TODO: Prevent duplicate requests from the same user
    """Request premium.

    Records or acknowledges a request for premium access.

    Args:
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_basic).

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        NotImplementedError: When the endpoint is a documented future implementation stub."""
    raise NotImplementedError
