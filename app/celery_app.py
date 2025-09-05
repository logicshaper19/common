"""
Celery application configuration for background job processing.
"""
from celery import Celery

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

# Configure logging for Celery
configure_logging()
logger = get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "common",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.services.transparency",
        "app.services.transparency_jobs",
        "app.services.notifications",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.services.transparency.*": {"queue": "transparency"},
    "app.services.transparency_jobs.*": {"queue": "transparency"},
    "app.services.notifications.*": {"queue": "notifications"},
}

logger.info("Celery application configured", broker=settings.redis_url)
