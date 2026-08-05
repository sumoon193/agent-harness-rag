"""Runtime 候选依赖的端口契约，不引用 HR/RAG 领域接口。

端口只使用领域中性类型（聚合记录、事件载荷、时钟），使 Runtime Kernel
候选通过本层依赖边界接入外部存储与时间，而不是直接耦合业务领域类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.devmate.contracts.state import CaseStatus


@dataclass(frozen=True)
class CaseRecord:
    """领域中性的聚合记录。"""

    case_id: str
    status: CaseStatus
    version: int
    actor_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class EventStreamPort(Protocol):
    """append-only 事件流端口。"""

    async def append(
        self,
        *,
        aggregate_id: str,
        aggregate_type: str,
        event_type: str,
        payload: dict[str, Any],
        command_id: str,
        expected_version: int,
        actor_id: str,
    ) -> None: ...

    async def load_stream(self, aggregate_id: str) -> list[dict[str, Any]]: ...


class CaseStorePort(Protocol):
    """Case 聚合存储端口。"""

    async def get(self, case_id: str) -> CaseRecord | None: ...

    async def upsert(self, record: CaseRecord) -> None: ...


class ClockPort(Protocol):
    """确定性的时间端口，供 Runtime 候选注入。"""

    def now(self) -> datetime: ...
