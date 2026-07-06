"""入库任务状态存储。"""
from __future__ import annotations

from typing import Protocol

import redis

from app.services.ingestion.task import IngestionTask


class IngestionTaskStore(Protocol):
    """入库任务状态存储协议。"""

    def save(self, task: IngestionTask) -> None:
        """保存或覆盖任务状态。"""
        ...

    def get(self, task_id: str) -> IngestionTask | None:
        """按任务 ID 读取任务状态。"""
        ...

    def clear(self) -> None:
        """清空任务状态，主要供测试使用。"""
        ...


class InMemoryIngestionTaskStore:
    """进程内任务状态存储，用于 fallback 和单元测试。"""

    def __init__(self) -> None:
        self._tasks: dict[str, IngestionTask] = {}

    def save(self, task: IngestionTask) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: str) -> IngestionTask | None:
        return self._tasks.get(task_id)

    def clear(self) -> None:
        self._tasks.clear()


class RedisIngestionTaskStore:
    """Redis 任务状态存储，用于 API 进程和 Celery worker 共享状态。"""

    def __init__(
        self,
        redis_url: str,
        *,
        key_prefix: str = "ingestion:task",
        ttl_seconds: int = 86_400,
    ) -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def save(self, task: IngestionTask) -> None:
        self._redis.set(
            self._key(task.id),
            task.model_dump_json(),
            ex=self._ttl_seconds,
        )

    def get(self, task_id: str) -> IngestionTask | None:
        raw = self._redis.get(self._key(task_id))
        if raw is None:
            return None
        return IngestionTask.model_validate_json(raw)

    def clear(self) -> None:
        for key in self._redis.scan_iter(f"{self._key_prefix}:*"):
            self._redis.delete(key)

    def _key(self, task_id: str) -> str:
        return f"{self._key_prefix}:{task_id}"
