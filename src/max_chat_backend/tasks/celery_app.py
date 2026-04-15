from celery import Celery

from max_chat_backend.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "max_chat_backend",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["max_chat_backend.tasks.workflows"],
)
celery_app.conf.task_track_started = True
celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.result_serializer = "json"

