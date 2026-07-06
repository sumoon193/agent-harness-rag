"""Celery 应用配置。"""
from __future__ import annotations

from celery import Celery

from app.config import Settings, get_settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    """创建 Celery app。"""
    settings = settings or get_settings()
    broker_url = settings.celery_broker_url or settings.redis_url
    result_backend = settings.celery_result_backend or settings.redis_url

    celery_app = Celery(
        "enterprisemind",
        broker=broker_url,
        backend=result_backend,
        include=["app.services.ingestion.celery_tasks"],
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_always_eager=settings.celery_task_always_eager,
        task_eager_propagates=True,
    )
    return celery_app


celery_app = create_celery_app()
