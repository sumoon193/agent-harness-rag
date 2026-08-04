"""devmate Runtime 领域中性数据模型。

事件、Outbox 消息与 Case 记录只携带可审计字段，不引用任何 HR/RAG
领域接口；Checkpoint 以 checkpoint_id 作为幂等键保证重放安全。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class Clock(Protocol):
    """确定性时间来源。"""

    def now(self) -> str: ...


@dataclass(frozen=True)
class FixedClock:
    """固定确定性时钟，默认用于测试与重放。"""

    timestamp: str = "2026-08-04T00:00:00Z"

    def now(self) -> str:
        return self.timestamp


@dataclass(frozen=True)
class StoredEvent:
    """追加式事件流中的单条事件。"""

    event_id: str
    aggregate_id: str
    aggregate_type: str
    version: int
    event_type: str
    payload: dict[str, Any]
    checkpoint_id: str
    actor_id: str
    created_at: str


@dataclass(frozen=True)
class OutboxMessage:
    """与事件同事务落库的 Outbox 消息。"""

    outbox_id: str
    checkpoint_id: str
    aggregate_id: str
    event_type: str
    topic: str
    payload: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class CaseRecord:
    """devmate_case 聚合记录：主键、版本/幂等键、时间与审计来源。"""

    case_id: str
    version: int
    checkpoint_id: str
    status: str
    created_at: str
    updated_at: str
    audit_source: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DM03Input:
    """Checkpoint 的 typed 输入。"""

    checkpoint_id: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]
    expected_version: int
    actor_id: str
    aggregate_type: str = "devmate_case"
    status: str = "created"
    outbox_topics: tuple[str, ...] = ()
    audit_source: str = ""


@dataclass(frozen=True)
class DM03Result:
    """Checkpoint 的 typed 结果。"""

    checkpoint_id: str
    new_version: int
    outbox_ids: tuple[str, ...]
    projection: dict[str, Any]
