from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User, UserRole
from app.schemas.user import UserAdminView

router = APIRouter()

DBDep = Annotated[Session, Depends(get_db)]
AdminUserDep = Annotated[User, Depends(require_admin)]


@router.get("/users", response_model=list[UserAdminView])
def list_users(
    db: DBDep,
    current_user: AdminUserDep,
    page:      int        = Query(1,  ge=1),
    page_size: int        = Query(50, ge=1, le=200),
    search:    str | None = None,
):
    # TODO: Paginated user list; search on email and display_name
    raise NotImplementedError


@router.patch("/users/{user_id}/role")
def update_user_role(user_id: int, role: UserRole, db: DBDep, current_user: AdminUserDep):
    # TODO: Fetch user, update role, commit
    # TODO: Prevent admin from demoting themselves
    # TODO: Return updated UserAdminView
    raise NotImplementedError


@router.get("/premium-requests")
def list_premium_requests(db: DBDep, current_user: AdminUserDep):
    # TODO: Return pending PremiumRequest records (model not yet created)
    raise NotImplementedError


@router.post("/premium-requests/{request_id}/approve", status_code=204)
def approve_premium_request(request_id: int, db: DBDep, current_user: AdminUserDep):
    # TODO: Promote target user to PREMIUM
    # TODO: Mark request as resolved / delete it
    raise NotImplementedError


@router.get("/metrics")
def get_metrics(db: DBDep, current_user: AdminUserDep):
    # TODO: Return dict with: total_users, active_users, basic_count, premium_count,
    #       recommendations_served, feedback_helpful_pct, api_usage_today
    raise NotImplementedError


@router.get("/pipeline/status")
def get_pipeline_status(current_user: AdminUserDep):
    # TODO: Query Redis / Celery result backend for last rawg_sync task result
    # TODO: Return last_run, status ("success"/"failure"), next_scheduled_run
    raise NotImplementedError


@router.post("/pipeline/trigger", status_code=202)
def trigger_pipeline(current_user: AdminUserDep):
    # TODO: Dispatch rawg_sync.sync_games Celery task
    # TODO: Return task_id so admin can poll status
    raise NotImplementedError
