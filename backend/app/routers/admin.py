from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User, UserRole
from app.schemas.user import UserAdminView
from app.services import admin_service
from app.services import kv_store

router = APIRouter()

DBDep        = Annotated[Session, Depends(get_db)]
AdminUserDep = Annotated[User,    Depends(require_admin)]

_PIPELINE_KEY = "rawg_sync:last_run"


@router.get("/users", response_model=list[UserAdminView])
def list_users(
    db:         DBDep,
    current_user: AdminUserDep,
    page:      int        = Query(1,  ge=1),
    page_size: int        = Query(50, ge=1, le=200),
    search:    str | None = None,
):
    """List users.

    Returns a paginated admin view of users, optionally filtered by search text.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.
        page: One-based page number to return. Defaults to 1.
        page_size: Maximum number of records to return per page. Defaults to Query(50, ge=1, le=200).
        search: Optional search text used to filter returned records. Defaults to None.

    Returns:
        Serialized response object or task result produced by the operation."""
    return admin_service.list_users(db, page, page_size, search)


@router.patch("/users/{user_id}/role", response_model=UserAdminView)
def update_user_role(
    user_id: int,
    role:    UserRole,
    db:      DBDep,
    current_user: AdminUserDep,
):
    """Update user role.

    Updates a target user role while preventing invalid self-demotion behavior in the service layer.

    Args:
        user_id: ID of the user being read or modified.
        role: Role value to apply to the selected user.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return admin_service.update_user_role(db, user_id, role, current_user.id)


@router.get("/premium-requests")
def list_premium_requests(db: DBDep, current_user: AdminUserDep):
    # PremiumRequest model not yet created — return empty list
    """List premium requests.

    Returns pending premium upgrade requests once that model exists.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return []


@router.post("/premium-requests/{request_id}/approve", status_code=204)
def approve_premium_request(request_id: int, db: DBDep, current_user: AdminUserDep):
    # TODO: Promote target user to PREMIUM once PremiumRequest model exists
    """Approve premium request.

    Reserved endpoint for approving a future premium upgrade request.

    Args:
        request_id: ID of the premium request being acted on.
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation.

    Raises:
        NotImplementedError: When the endpoint is a documented future implementation stub."""
    raise NotImplementedError


@router.get("/metrics")
def get_metrics(db: DBDep, current_user: AdminUserDep):
    """Get metrics.

    Delegates the request to the appropriate service layer and returns the serialized response.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    return admin_service.get_metrics(db)


@router.get("/pipeline/status")
def get_pipeline_status(current_user: AdminUserDep):
    """Get pipeline status.

    Returns the last RAWG pipeline status from the key-value store or a never-run fallback.

    Args:
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    try:
        status_payload = kv_store.get_json(_PIPELINE_KEY)
        if status_payload:
            return status_payload
    except Exception:
        pass
    return {"last_run": None, "status": "never_run", "task_id": None}


def _run_rawg_fargate_task() -> str:
    """Run rawg fargate task.

    Starts the configured ECS Fargate task that runs the RAWG catalog job in Lambda deployments.

    Returns:
        String value produced by the operation.

    Raises:
        RuntimeError: When required infrastructure or configuration is unavailable."""
    required = [
        settings.ECS_CLUSTER_ARN,
        settings.ECS_RAWG_TASK_DEFINITION_ARN,
        settings.ECS_SUBNET_IDS,
        settings.ECS_SECURITY_GROUP_IDS,
    ]
    if not all(required):
        raise RuntimeError("ECS RAWG task settings are incomplete")

    import boto3

    ecs = boto3.client("ecs", region_name=settings.AWS_REGION)
    response = ecs.run_task(
        cluster=settings.ECS_CLUSTER_ARN,
        taskDefinition=settings.ECS_RAWG_TASK_DEFINITION_ARN,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": settings.ECS_SUBNET_IDS,
                "securityGroups": settings.ECS_SECURITY_GROUP_IDS,
                "assignPublicIp": "ENABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": settings.ECS_RAWG_CONTAINER_NAME,
                    "command": [
                        "python",
                        "-m",
                        "app.jobs.rawg_job",
                        "sync-catalog",
                        "--max-requests",
                        str(settings.RAWG_MONTHLY_REQUEST_BUDGET),
                    ],
                }
            ]
        },
    )
    failures = response.get("failures") or []
    if failures:
        raise RuntimeError(str(failures[0]))
    tasks = response.get("tasks") or []
    if not tasks:
        raise RuntimeError("ECS did not start a RAWG task")
    return tasks[0]["taskArn"]


@router.post("/pipeline/trigger", status_code=202)
def trigger_pipeline(current_user: AdminUserDep):
    """Trigger pipeline.

    Dispatches the RAWG catalog pipeline through ECS or Celery and records the trigger status.

    Args:
        current_user: Authenticated user supplied by the route dependency.

    Returns:
        Serialized response object or task result produced by the operation."""
    try:
        if settings.APP_RUNTIME == "lambda":
            task_id = _run_rawg_fargate_task()
        else:
            from app.workers.tasks.rawg_sync import sync_catalog
            task = sync_catalog.delay()
            task_id = task.id
    except Exception:
        task_id = None

    # Record trigger time in Redis regardless of whether the task dispatched
    payload = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "status":   "triggered",
        "task_id":  task_id,
    }
    try:
        kv_store.set_json(_PIPELINE_KEY, payload)
    except Exception:
        pass

    return {"task_id": task_id}
