from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.recommendation import Recommendation, RecommendationFeedback, RecommendationItem
from app.models.user import User
from app.schemas.recommendation import FeedbackCreate

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # Verify the item belongs to one of the current user's recommendations.
    item: RecommendationItem | None = (
        db.query(RecommendationItem)
        .join(RecommendationItem.recommendation)
        .filter(
            RecommendationItem.id == feedback.item_id,
            Recommendation.user_id == current_user.id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation item not found.",
        )

    # Upsert: update existing feedback or create a new one.
    existing: RecommendationFeedback | None = (
        db.query(RecommendationFeedback)
        .filter(RecommendationFeedback.item_id == feedback.item_id)
        .first()
    )
    if existing:
        existing.is_helpful = feedback.is_helpful
    else:
        db.add(RecommendationFeedback(
            item_id=feedback.item_id,
            is_helpful=feedback.is_helpful,
        ))

    db.commit()
    return {"detail": "Feedback recorded."}
