"""Celery application configuration and tasks."""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "conversation_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.celery_app.tasks.session_tasks",
        "app.celery_app.tasks.attachment_tasks",
        "app.celery_app.tasks.action_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "archive-inactive-sessions": {
        "task": "app.celery_app.tasks.session_tasks.archive_inactive_sessions",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "cleanup-old-attachments": {
        "task": "app.celery_app.tasks.attachment_tasks.cleanup_old_attachments",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Weekly Sunday at 3 AM
    },
}


@celery_app.task
def health_check():
    """Health check task for monitoring."""
    return {"status": "healthy"}