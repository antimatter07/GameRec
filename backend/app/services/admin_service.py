from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.library import LibraryEntry
from app.models.recommendation import Recommendation, RecommendationFeedback
from app.models.user import User, UserRole


def list_users(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
) -> list[User]:
    """List users.

    Builds the database query, applies caller-provided filters, and returns the requested slice of results.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        page: One-based page number to return. Defaults to 1.
        page_size: Maximum number of records to return per page.
        search: Optional text used to filter records by name or other searchable fields. Defaults to None.

    Returns:
        List of matching records or serialized service objects."""
    query = db.query(User)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(User.email.ilike(pattern), User.display_name.ilike(pattern))
        )
    return query.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()


def update_user_role(
    db: Session,
    user_id: int,
    role: UserRole,
    current_user_id: int,
) -> User:
    """Update user role.

    Applies validated field changes to an existing record and commits the updated state.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        role: Role value to apply to the selected user.
        current_user_id: current user id value used by the operation.

    Returns:
        User produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role.",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def get_metrics(db: Session) -> dict:
    """Get metrics.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        Dictionary containing serialized service state and metadata."""
    active_cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    total_users   = db.query(func.count(User.id)).scalar() or 0
    active_users  = db.query(func.count(User.id)).filter(User.updated_at >= active_cutoff).scalar() or 0
    basic_count   = db.query(func.count(User.id)).filter(User.role == UserRole.BASIC).scalar() or 0
    premium_count = db.query(func.count(User.id)).filter(User.role == UserRole.PREMIUM).scalar() or 0

    recommendations_served = db.query(func.count(Recommendation.id)).scalar() or 0

    total_feedback   = db.query(func.count(RecommendationFeedback.id)).scalar() or 0
    helpful_feedback = (
        db.query(func.count(RecommendationFeedback.id))
        .filter(RecommendationFeedback.is_helpful.is_(True))
        .scalar() or 0
    )
    feedback_helpful_pct = (
        round(helpful_feedback / total_feedback * 100, 1) if total_feedback > 0 else None
    )

    return {
        "total_users":            total_users,
        "active_users":           active_users,
        "basic_count":            basic_count,
        "premium_count":          premium_count,
        "recommendations_served": recommendations_served,
        "feedback_helpful_pct":   feedback_helpful_pct,
    }
