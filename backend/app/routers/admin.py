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
    return admin_service.list_users(db, page, page_size, search)


@router.patch("/users/{user_id}/role", response_model=UserAdminView)
def update_user_role(
    user_id: int,
    role:    UserRole,
    db:      DBDep,
    current_user: AdminUserDep,
):
    return admin_service.update_user_role(db, user_id, role, current_user.id)


@router.get("/premium-requests")
def list_premium_requests(db: DBDep, current_user: AdminUserDep):
    # PremiumRequest model not yet created — return empty list
    return []


@router.post("/premium-requests/{request_id}/approve", status_code=204)
def approve_premium_request(request_id: int, db: DBDep, current_user: AdminUserDep):
    # TODO: Promote target user to PREMIUM once PremiumRequest model exists
    raise NotImplementedError


@router.get("/metrics")
def get_metrics(db: DBDep, current_user: AdminUserDep):
    return admin_service.get_metrics(db)


@router.get("/pipeline/status")
def get_pipeline_status(current_user: AdminUserDep):
    try:
        status_payload = kv_store.get_json(_PIPELINE_KEY)
        if status_payload:
            return status_payload
    except Exception:
        pass
    return {"last_run": None, "status": "never_run", "task_id": None}


def _run_rawg_fargate_task() -> str:
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
