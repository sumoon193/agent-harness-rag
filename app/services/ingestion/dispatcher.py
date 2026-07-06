"""入库任务调度器。"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from app.services.ingestion.job import IngestionJobPayload
from app.services.ingestion.store import IngestionTaskStore
from app.services.ingestion.task import IngestionTask

ExecutionMode = Literal["sync", "celery"]
PipelineRunner = Callable[[IngestionJobPayload], Awaitable[IngestionTask]]
CeleryEnqueue = Callable[[dict[str, Any]], None]


class IngestionDispatcher:
    """根据配置选择同步入库或 Celery 异步入库。"""

    def __init__(
        self,
        *,
        execution_mode: ExecutionMode,
        task_store: IngestionTaskStore,
        pipeline_runner: PipelineRunner,
        celery_enqueue: CeleryEnqueue | None = None,
    ) -> None:
        self._execution_mode = execution_mode
        self._task_store = task_store
        self._pipeline_runner = pipeline_runner
        self._celery_enqueue = celery_enqueue or _default_celery_enqueue

    async def dispatch(
        self,
        *,
        task: IngestionTask,
        tenant_id: str,
        department_id: str,
        visibility: str,
    ) -> IngestionTask:
        """调度入库任务并返回当前可见状态。"""
        payload = IngestionJobPayload(
            task=task,
            tenant_id=tenant_id,
            department_id=department_id,
            visibility=visibility,
        )
        self._task_store.save(task)

        if self._execution_mode == "celery":
            self._celery_enqueue(payload.model_dump(mode="json"))
            return self._task_store.get(task.id) or task

        result = await self._pipeline_runner(payload)
        self._task_store.save(result)
        return result


def _default_celery_enqueue(payload: dict[str, Any]) -> None:
    """默认 Celery 入队函数（使用阶段级 task chain）。"""
    from app.services.ingestion.celery_tasks import dispatch_ingestion_chain

    dispatch_ingestion_chain(payload)
