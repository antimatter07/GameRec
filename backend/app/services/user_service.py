from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, user_in: UserCreate) -> User:
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        display_name=user_in.display_name,
        role=UserRole.BASIC,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, updates: UserUpdate) -> User:
    # TODO: Iterate updates.model_dump(exclude_unset=True).items() and setattr
    # TODO: db.commit(); db.refresh(user); return user
    raise NotImplementedError


def delete_user(db: Session, user: User) -> None:
    """GDPR-compliant deletion — choose hard-delete or anonymization."""
    # Option A – Hard delete (cascades to library and recommendations via FK):
    # TODO: db.delete(user); db.commit()

    # Option B – Anonymize (keeps statistical data, removes PII):
    # TODO: user.email = f"deleted_{user.id}@deleted"
    # TODO: user.hashed_password = ""
    # TODO: user.display_name = None; user.avatar_url = None; user.bio = None
    # TODO: user.is_active = False; db.commit()
    raise NotImplementedError
