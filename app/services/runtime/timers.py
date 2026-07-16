"""持久化定时器接口的 deterministic in-memory 实现。"""
from __future__ import annotations

import uuid
from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.enums import TimerStatus
from app.schemas.runtime import DurableTimer
from app.services.runtime.clock import Clock, SystemClock


class InMemoryTimerStore:
    """通过 claim 状态防止多个 scheduler 重复触发 timer。"""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._timers: dict[str, DurableTimer] = {}
        self._by_key: dict[str, str] = {}

    async def schedule(
        self,
        *,
        case_id: str,
        timer_type: str,
        due_at: datetime,
        payload: dict[str, object],
        idempotency_key: str,
    ) -> DurableTimer:
        """幂等调度 timer。"""
        existing_id = self._by_key.get(idempotency_key)
        if existing_id is not None:
            return await self.get(existing_id)
        if due_at.tzinfo is None:
            raise ValidationError("Timer due_at must be timezone-aware")
        timer = DurableTimer(
            id=f"timer_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            timer_type=timer_type,
            due_at=due_at,
            payload=dict(payload),
            idempotency_key=idempotency_key,
            created_at=self._clock.now(),
        )
        self._timers[timer.id] = timer
        self._by_key[idempotency_key] = timer.id
        return timer.model_copy(deep=True)

    async def claim_due(
        self,
        *,
        owner_id: str,
        limit: int,
        now: datetime | None = None,
    ) -> list[DurableTimer]:
        """原子 claim 到期且未处理的 timer。"""
        claimed_at = now or self._clock.now()
        due = sorted(
            (
                timer
                for timer in self._timers.values()
                if timer.status == TimerStatus.SCHEDULED and timer.due_at <= claimed_at
            ),
            key=lambda item: (item.due_at, item.id),
        )[:limit]
        for timer in due:
            timer.status = TimerStatus.CLAIMED
            timer.claimed_by = owner_id
            timer.claimed_at = claimed_at
        return [timer.model_copy(deep=True) for timer in due]

    async def mark_fired(
        self,
        timer_id: str,
        *,
        owner_id: str,
        now: datetime | None = None,
    ) -> DurableTimer:
        """由 claim owner 确认 timer 已触发。"""
        timer = self._get(timer_id)
        if timer.status != TimerStatus.CLAIMED or timer.claimed_by != owner_id:
            raise ValidationError(f"Timer is not claimed by {owner_id}: {timer_id}")
        timer.status = TimerStatus.FIRED
        timer.fired_at = now or self._clock.now()
        return timer.model_copy(deep=True)

    async def get(self, timer_id: str) -> DurableTimer:
        """查询 timer。"""
        return self._get(timer_id).model_copy(deep=True)

    def _get(self, timer_id: str) -> DurableTimer:
        timer = self._timers.get(timer_id)
        if timer is None:
            raise NotFoundError(f"Timer not found: {timer_id}")
        return timer
