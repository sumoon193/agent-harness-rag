"""Effectively-once 副作用账本。"""
from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.enums import SideEffectStatus
from app.schemas.runtime import SideEffectRecord
from app.services.runtime.clock import Clock, SystemClock


class InMemorySideEffectLedger:
    """记录副作用 reservation、结果和未知状态的 deterministic fake。"""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._records: dict[str, SideEffectRecord] = {}
        self._by_key: dict[str, str] = {}

    async def reserve(
        self,
        *,
        idempotency_key: str,
        tool_name: str,
        subject_hash: str,
    ) -> SideEffectRecord:
        """预留副作用；相同语义的重复调用返回原记录。"""
        existing_id = self._by_key.get(idempotency_key)
        if existing_id is not None:
            existing = self._records[existing_id]
            if existing.tool_name != tool_name or existing.subject_hash != subject_hash:
                raise ValidationError(
                    f"Idempotency key reused with different side effect: {idempotency_key}"
                )
            return existing.model_copy(deep=True)

        now = self._clock.now()
        record = SideEffectRecord(
            id=f"effect_{uuid.uuid4().hex[:12]}",
            idempotency_key=idempotency_key,
            tool_name=tool_name,
            subject_hash=subject_hash,
            created_at=now,
            updated_at=now,
        )
        self._records[record.id] = record
        self._by_key[idempotency_key] = record.id
        return record.model_copy(deep=True)

    async def mark_succeeded(
        self,
        record_id: str,
        result: dict[str, object],
    ) -> SideEffectRecord:
        """记录确定成功的外部结果。"""
        record = self._get(record_id)
        record.status = SideEffectStatus.SUCCEEDED
        record.result = dict(result)
        record.error = None
        record.updated_at = self._clock.now()
        return record.model_copy(deep=True)

    async def mark_unknown(self, record_id: str, error: str) -> SideEffectRecord:
        """标记请求结果未知，等待 reconciliation。"""
        record = self._get(record_id)
        record.status = SideEffectStatus.UNKNOWN
        record.error = error
        record.updated_at = self._clock.now()
        return record.model_copy(deep=True)

    async def list_records(self) -> list[SideEffectRecord]:
        """列出账本记录副本。"""
        return [record.model_copy(deep=True) for record in self._records.values()]

    def _get(self, record_id: str) -> SideEffectRecord:
        record = self._records.get(record_id)
        if record is None:
            raise NotFoundError(f"Side effect record not found: {record_id}")
        return record
