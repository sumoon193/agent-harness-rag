"""定时器与长期 Case 事件之间的应用服务。"""
from __future__ import annotations

from datetime import datetime

from app.schemas.runtime import DurableTimer, TimerScheduleResult
from app.services.runtime.case_service import CaseService
from app.services.runtime.interfaces import TimerStore


class TimerCoordinator:
    """调度 timer，并用幂等 Case 事件驱动跨天唤醒。"""

    def __init__(
        self,
        *,
        case_service: CaseService,
        timer_store: TimerStore,
    ) -> None:
        self._case_service = case_service
        self._timer_store = timer_store

    async def schedule(
        self,
        *,
        case_id: str,
        timer_type: str,
        due_at: datetime,
        payload: dict[str, object],
        actor_id: str,
        command_id: str,
        expected_version: int,
    ) -> TimerScheduleResult:
        """调度 timer 并记录 Case 等待事件。"""
        timer = await self._timer_store.schedule(
            case_id=case_id,
            timer_type=timer_type,
            due_at=due_at,
            payload=payload,
            idempotency_key=f"{case_id}:{command_id}",
        )
        case = await self._case_service.record_timer_scheduled(
            timer=timer,
            actor_id=actor_id,
            command_id=command_id,
            expected_version=expected_version,
        )
        return TimerScheduleResult(timer=timer, case=case)

    async def fire_due(self, *, owner_id: str, limit: int) -> list[DurableTimer]:
        """claim 到期 timer，追加唤醒事件后确认 fired。"""
        claimed = await self._timer_store.claim_due(owner_id=owner_id, limit=limit)
        fired: list[DurableTimer] = []
        for timer in claimed:
            case = await self._case_service.get_case(timer.case_id)
            await self._case_service.record_timer_fired(
                timer=timer,
                actor_id=owner_id,
                expected_version=case.version,
            )
            fired.append(
                await self._timer_store.mark_fired(timer.id, owner_id=owner_id)
            )
        return fired
