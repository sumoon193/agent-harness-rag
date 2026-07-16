"""Agent Runtime 事件与执行治理 Schema。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import CaseStatus, SideEffectStatus, TimerStatus


class ExecutionManifest(BaseModel):
    """固定一次 Case/Run 所使用的可执行组件版本。"""

    model_provider: str
    model_name: str
    model_version: str
    prompt_version: str
    skill_versions: dict[str, str] = Field(default_factory=dict)
    tool_schema_versions: dict[str, str] = Field(default_factory=dict)
    policy_version: str
    retrieval_version: str
    context_strategy_version: str
    code_version: str


class HRCase(BaseModel):
    """HR Shared Service reference application 的长期 Case projection。"""

    id: str = Field(description="Case ID，前缀 case_")
    title: str
    tenant_id: str
    subject_user_id: str
    status: CaseStatus = CaseStatus.OPEN
    version: int = Field(ge=1)
    execution_manifest: ExecutionManifest
    policy_versions: dict[str, str] = Field(default_factory=dict)
    working_memory: dict[str, Any] = Field(default_factory=dict)
    active_run_id: str | None = None
    created_at: datetime
    updated_at: datetime


class RunEventEnvelope(BaseModel):
    """append-only Event Store 中的标准事件信封。"""

    id: str = Field(description="事件 ID，前缀 evt_")
    aggregate_id: str = Field(description="聚合 ID，例如 case_id")
    aggregate_type: str = Field(description="聚合类型")
    sequence: int = Field(ge=1, description="聚合内单调递增序号")
    event_type: str = Field(description="事件类型")
    payload: dict[str, Any] = Field(default_factory=dict, description="事件数据")
    command_id: str = Field(description="产生事件的幂等命令 ID")
    actor_id: str = Field(description="操作主体 ID")
    created_at: datetime = Field(description="事件发生时间（UTC）")
    schema_version: int = Field(default=1, ge=1, description="事件 schema 版本")
    prev_hash: str = Field(default="", description="前一事件哈希")
    event_hash: str = Field(description="当前事件审计哈希")


class OutboxMessage(BaseModel):
    """与领域事件同批产生的可靠投递消息。"""

    id: str = Field(description="Outbox ID，前缀 outbox_")
    event_id: str = Field(description="关联领域事件 ID")
    aggregate_id: str = Field(description="关联聚合 ID")
    sequence: int = Field(ge=1, description="关联事件序号")
    topic: str = Field(description="投递主题")
    payload: dict[str, Any] = Field(default_factory=dict, description="投递数据")
    created_at: datetime = Field(description="创建时间（UTC）")
    published_at: datetime | None = Field(default=None, description="确认投递时间")
    claimed_by: str | None = Field(default=None, description="当前投递 worker")
    claimed_at: datetime | None = Field(default=None, description="投递 claim 时间")
    delivery_attempts: int = Field(default=0, ge=0, description="投递尝试次数")


class RunLease(BaseModel):
    """带 fencing token 的运行租约。"""

    resource_id: str
    owner_id: str
    acquired_at: datetime
    expires_at: datetime
    fencing_token: int = Field(ge=1)


class SideEffectRecord(BaseModel):
    """外部副作用调用的 effectively-once 账本记录。"""

    id: str = Field(description="账本 ID，前缀 effect_")
    idempotency_key: str
    tool_name: str
    subject_hash: str
    status: SideEffectStatus = SideEffectStatus.RESERVED
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class DurableTimer(BaseModel):
    """用于 SLA、审批过期和长期流程唤醒的定时器。"""

    id: str = Field(description="Timer ID，前缀 timer_")
    case_id: str
    timer_type: str
    due_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str
    status: TimerStatus = TimerStatus.SCHEDULED
    claimed_by: str | None = None
    claimed_at: datetime | None = None
    fired_at: datetime | None = None
    created_at: datetime


class TimerScheduleResult(BaseModel):
    """定时器调度后返回的 timer 与 Case projection。"""

    timer: DurableTimer
    case: HRCase


class RuntimeMetricsSnapshot(BaseModel):
    """可导出到 OTel/Phoenix 或控制台的运行指标快照。"""

    counters: dict[str, int] = Field(default_factory=dict)
    gauges: dict[str, float] = Field(default_factory=dict)
    observations: dict[str, list[float]] = Field(default_factory=dict)
    generated_at: datetime
