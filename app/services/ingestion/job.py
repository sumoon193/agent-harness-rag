"""Celery 入库任务负载模型。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.ingestion.task import IngestionTask


class IngestionJobPayload(BaseModel):
    """worker 执行入库所需的最小负载。"""

    task: IngestionTask
    tenant_id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    visibility: str = Field(default="department")
