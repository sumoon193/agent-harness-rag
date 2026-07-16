"""Agent Runtime 可替换持久化边界。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.schemas.runtime import (
    DurableTimer,
    HRCase,
    OutboxMessage,
    RunEventEnvelope,
    RunLease,
    SideEffectRecord,
)


class EventStore(Protocol):
    """append-only event stream 与 transactional outbox 契约。"""

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
    ) -> RunEventEnvelope: ...

    async def load_stream(self, aggregate_id: str) -> list[RunEventEnvelope]: ...

    async def verify_chain(self, aggregate_id: str) -> bool: ...

    async def pending_outbox(self, *, limit: int = 100) -> list[OutboxMessage]: ...

    async def claim_outbox(
        self,
        *,
        owner_id: str,
        limit: int,
        claim_ttl_seconds: int = 30,
    ) -> list[OutboxMessage]: ...

    async def mark_outbox_published(self, outbox_id: str, *, owner_id: str) -> None: ...


class CaseProjectionStore(Protocol):
    """Case 查询 projection 的幂等存储契约。"""

    async def get(self, case_id: str) -> HRCase | None: ...

    async def upsert(self, case: HRCase) -> None: ...

    async def list(self, *, limit: int = 100) -> list[HRCase]: ...


class LeaseStore(Protocol):
    """带 fencing token 的跨 worker lease 契约。"""

    async def acquire(
        self,
        resource_id: str,
        owner_id: str,
        *,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> RunLease: ...

    async def release(
        self,
        resource_id: str,
        owner_id: str,
        fencing_token: int,
    ) -> None: ...


class SideEffectLedger(Protocol):
    """effectively-once 外部写操作账本契约。"""

    async def reserve(
        self,
        *,
        idempotency_key: str,
        tool_name: str,
        subject_hash: str,
    ) -> SideEffectRecord: ...

    async def mark_succeeded(
        self,
        record_id: str,
        result: dict[str, object],
    ) -> SideEffectRecord: ...

    async def mark_unknown(self, record_id: str, error: str) -> SideEffectRecord: ...

    async def list_records(self) -> list[SideEffectRecord]: ...


class TimerStore(Protocol):
    """可 claim、可恢复的 durable timer 契约。"""

    async def schedule(
        self,
        *,
        case_id: str,
        timer_type: str,
        due_at: datetime,
        payload: dict[str, object],
        idempotency_key: str,
    ) -> DurableTimer: ...

    async def claim_due(
        self,
        *,
        owner_id: str,
        limit: int,
        now: datetime | None = None,
    ) -> list[DurableTimer]: ...

    async def mark_fired(
        self,
        timer_id: str,
        *,
        owner_id: str,
        now: datetime | None = None,
    ) -> DurableTimer: ...

    async def get(self, timer_id: str) -> DurableTimer: ...
