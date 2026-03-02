from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.recommendation import FeedbackCreate

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Verify feedback.item_id belongs to one of current_user's recommendations
    # TODO: Upsert RecommendationFeedback (allow changing vote)
    # TODO: (Optional) Dispatch Celery task to update model weights based on feedback
    raise NotImplementedError
