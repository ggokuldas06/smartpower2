from celery import Celery

celery_service = Celery(
    "mailing_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
