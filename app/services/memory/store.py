"""Episodic Memory Store 的 ACL-aware deterministic fallback。"""
from __future__ import annotations

import uuid
from datetime import timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import NotFoundError, PermissionError, ValidationError
from app.models.runtime import EpisodicMemoryRecordORM
from app.schemas.enums import MemoryStatus
from app.schemas.memory import EpisodicMemoryRecord
from app.services.runtime.clock import Clock, SystemClock
from app.services.security.prompt_guard import PromptGuard


class EpisodicMemoryStore(Protocol):
    """带 ACL、provenance 和删除语义的长期记忆边界。"""

    async def remember(
        self,
        *,
        tenant_id: str,
        case_id: str,
        memory_key: str,
        content: str,
        provenance_event_ids: list[str],
    ) -> EpisodicMemoryRecord: ...

    async def search(
        self,
        *,
        tenant_id: str,
        query: str,
    ) -> list[EpisodicMemoryRecord]: ...

    async def forget(
        self,
        memory_id: str,
        *,
        tenant_id: str,
    ) -> EpisodicMemoryRecord: ...

    async def get(
        self,
        memory_id: str,
        *,
        tenant_id: str,
    ) -> EpisodicMemoryRecord: ...


class InMemoryEpisodicMemoryStore:
    """隔离租户、保留 provenance 并支持 quarantine/forget 的内存实现。"""

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        prompt_guard: PromptGuard | None = None,
    ) -> None:
        self._clock = clock or SystemClock()
        self._prompt_guard = prompt_guard or PromptGuard()
        self._records: dict[str, EpisodicMemoryRecord] = {}

    async def remember(
        self,
        *,
        tenant_id: str,
        case_id: str,
        memory_key: str,
        content: str,
        provenance_event_ids: list[str],
    ) -> EpisodicMemoryRecord:
        """写入带来源的经验，注入内容只进入 quarantine。"""
        if not provenance_event_ids:
            raise ValidationError("Episodic memory requires provenance events")
        is_injection, reason = self._prompt_guard.detect_injection(content)
        now = self._clock.now()
        record = EpisodicMemoryRecord(
            id=f"mem_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            case_id=case_id,
            memory_key=memory_key,
            content=content,
            provenance_event_ids=provenance_event_ids,
            status=(MemoryStatus.QUARANTINED if is_injection else MemoryStatus.ACTIVE),
            poisoning_reason=reason or None,
            created_at=now,
            updated_at=now,
        )
        self._records[record.id] = record
        return record.model_copy(deep=True)

    async def search(
        self,
        *,
        tenant_id: str,
        query: str,
    ) -> list[EpisodicMemoryRecord]:
        """只召回当前租户 active 且与查询直接匹配的经验。"""
        query_terms = [term for term in query.lower().split() if term]
        return [
            record.model_copy(deep=True)
            for record in self._records.values()
            if record.tenant_id == tenant_id
            and record.status == MemoryStatus.ACTIVE
            and (
                query.lower() in record.content.lower()
                or any(term in record.content.lower() for term in query_terms)
            )
        ]

    async def forget(
        self,
        memory_id: str,
        *,
        tenant_id: str,
    ) -> EpisodicMemoryRecord:
        """逻辑删除记忆并保留审计记录。"""
        record = self._authorized(memory_id, tenant_id)
        record.status = MemoryStatus.DELETED
        record.updated_at = self._clock.now()
        return record.model_copy(deep=True)

    async def get(
        self,
        memory_id: str,
        *,
        tenant_id: str,
    ) -> EpisodicMemoryRecord:
        """按租户查询单条记忆，包括已删除状态。"""
        return self._authorized(memory_id, tenant_id).model_copy(deep=True)

    def _authorized(self, memory_id: str, tenant_id: str) -> EpisodicMemoryRecord:
        record = self._records.get(memory_id)
        if record is None:
            raise NotFoundError(f"Memory not found: {memory_id}")
        if record.tenant_id != tenant_id:
            raise PermissionError(f"Memory tenant mismatch: {memory_id}")
        return record


class SqlAlchemyEpisodicMemoryStore:
    """PostgreSQL/SQLAlchemy episodic memory adapter。"""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        clock: Clock | None = None,
        prompt_guard: PromptGuard | None = None,
    ) -> None:
        self._sessions = session_factory
        self._clock = clock or SystemClock()
        self._prompt_guard = prompt_guard or PromptGuard()

    async def remember(
        self,
        *,
        tenant_id: str,
        case_id: str,
        memory_key: str,
        content: str,
        provenance_event_ids: list[str],
    ) -> EpisodicMemoryRecord:
        if not provenance_event_ids:
            raise ValidationError("Episodic memory requires provenance events")
        is_injection, reason = self._prompt_guard.detect_injection(content)
        now = self._clock.now()
        record = EpisodicMemoryRecordORM(
            id=f"mem_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            case_id=case_id,
            memory_key=memory_key,
            content=content,
            provenance_event_ids=provenance_event_ids,
            status=(
                MemoryStatus.QUARANTINED.value
                if is_injection
                else MemoryStatus.ACTIVE.value
            ),
            poisoning_reason=reason or None,
            created_at=now,
            updated_at=now,
        )
        async with self._sessions() as session:
            async with session.begin():
                session.add(record)
        return self._from_record(record)

    async def search(
        self,
        *,
        tenant_id: str,
        query: str,
    ) -> list[EpisodicMemoryRecord]:
        async with self._sessions() as session:
            records = list(
                (
                    await session.scalars(
                        select(EpisodicMemoryRecordORM).where(
                            EpisodicMemoryRecordORM.tenant_id == tenant_id,
                            EpisodicMemoryRecordORM.status == MemoryStatus.ACTIVE.value,
                        )
                    )
                ).all()
            )
        query_terms = [term for term in query.lower().split() if term]
        return [
            self._from_record(record)
            for record in records
            if query.lower() in record.content.lower()
            or any(term in record.content.lower() for term in query_terms)
        ]

    async def forget(
        self,
        memory_id: str,
        *,
        tenant_id: str,
    ) -> EpisodicMemoryRecord:
        async with self._sessions() as session:
            async with session.begin():
                record = await self._authorized(session, memory_id, tenant_id)
                record.status = MemoryStatus.DELETED.value
                record.updated_at = self._clock.now()
        return self._from_record(record)

    async def get(
        self,
        memory_id: str,
        *,
        tenant_id: str,
    ) -> EpisodicMemoryRecord:
        async with self._sessions() as session:
            record = await self._authorized(session, memory_id, tenant_id)
            return self._from_record(record)

    @staticmethod
    async def _authorized(
        session: AsyncSession,
        memory_id: str,
        tenant_id: str,
    ) -> EpisodicMemoryRecordORM:
        record = await session.get(EpisodicMemoryRecordORM, memory_id)
        if record is None:
            raise NotFoundError(f"Memory not found: {memory_id}")
        if record.tenant_id != tenant_id:
            raise PermissionError(f"Memory tenant mismatch: {memory_id}")
        return record

    @staticmethod
    def _from_record(record: EpisodicMemoryRecordORM) -> EpisodicMemoryRecord:
        created_at = record.created_at
        updated_at = record.updated_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        expires_at = record.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return EpisodicMemoryRecord(
            id=record.id,
            tenant_id=record.tenant_id,
            case_id=record.case_id,
            memory_key=record.memory_key,
            content=record.content,
            provenance_event_ids=list(record.provenance_event_ids),
            status=MemoryStatus(record.status),
            poisoning_reason=record.poisoning_reason,
            created_at=created_at,
            updated_at=updated_at,
            expires_at=expires_at,
        )
