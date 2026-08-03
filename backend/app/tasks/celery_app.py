from celery import Celery

from app.core import settings

celery_app = Celery("deplocker")
celery_app.conf.broker_url = (
    f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}"
    f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{settings.RABBITMQ_DEFAULT_VHOST}"
)
celery_app.conf.result_backend = f"redis://default:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(["app.tasks"])
