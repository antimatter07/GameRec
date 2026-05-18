from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "video_game_recommender",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.rawg_sync",
        "app.workers.tasks.recommendation",
        "app.workers.tasks.hltb_sync",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sync-rawg-monthly-catalog": {
            "task": "rawg_sync.sync_catalog",
            "schedule": crontab(day_of_month=1, hour=3, minute=0),
            "kwargs": {"max_requests": settings.RAWG_MONTHLY_REQUEST_BUDGET},
        },
        "sync-rawg-weekly-recent-releases": {
            "task": "rawg_sync.sync_recent_releases",
            "schedule": crontab(day_of_week=1, hour=3, minute=0),
            "kwargs": {"max_requests": settings.RAWG_RECENT_REQUEST_BUDGET, "days_back": 60},
        },
        "enrich-rawg-known-games-daily": {
            "task": "rawg_sync.enrich_known_games",
            "schedule": crontab(hour=3, minute=30),
            "kwargs": {"max_requests": settings.RAWG_DETAIL_REFRESH_REQUEST_BUDGET},
        },
    },
)
