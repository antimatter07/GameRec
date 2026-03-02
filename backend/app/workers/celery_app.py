from celery import Celery

from app.config import settings

celery_app = Celery(
    "video_game_recommender",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.rawg_sync",
        "app.workers.tasks.recommendation",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # TODO: Uncomment and configure the beat schedule once rawg_sync is implemented
    # from celery.schedules import crontab
    # beat_schedule={
    #     "sync-rawg-daily": {
    #         "task": "rawg_sync.sync_games",
    #         "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
    #         "args": (1, 50),  # page_start, page_end
    #     },
    # },
)
