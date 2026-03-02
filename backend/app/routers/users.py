from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_basic
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: Call user_service.update_user(db, current_user, updates)
    raise NotImplementedError


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: Call user_service.delete_user(db, current_user)
    # TODO: Ensure GDPR-compliant handling — anonymize or hard-delete per your policy
    raise NotImplementedError


@router.post("/me/request-premium", status_code=status.HTTP_202_ACCEPTED)
def request_premium(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Create a PremiumRequest record in the DB (model not yet created)
    # TODO: Optionally notify admin via email or in-app notification
    # TODO: Prevent duplicate requests from the same user
    raise NotImplementedError
