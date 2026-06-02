from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, user_in: UserCreate) -> User:
    """Create user.

    Validates the input, persists the relevant model changes, and returns the updated service representation.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_in: user in value used by the operation.

    Returns:
        User produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
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
    """Update user.

    Applies validated field changes to an existing record and commits the updated state.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user: Authenticated user model associated with the operation.
        updates: Validated update payload containing changed fields.

    Returns:
        User produced by the operation."""
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """Delete user.

    Verifies ownership or existence, removes the target record, and commits the change.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user: Authenticated user model associated with the operation.

    Returns:
        None."""
    db.delete(user)
    db.commit()
