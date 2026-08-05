"""devmate Case 内存存储：创建、推进与 timeline 追加。

case 记录携带主键、版本/幂等键与审计字段；command_id 幂等，重复命令不
产生重复 timeline 事件。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.devmate.cases.state import CaseStatus


class CaseNotFoundError(KeyError):
    def __init__(self, case_id: str) -> None:
        super().__init__(f"case not found: {case_id}")
        self.case_id = case_id


class DuplicateCaseError(ValueError):
    def __init__(self, case_id: str) -> None:
        super().__init__(f"case already exists: {case_id}")
        self.case_id = case_id


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    status: CaseStatus
    version: int
    actor_id: str
    created_at: str
    updated_at: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    case_id: str
    command_id: str
    event_type: str
    from_status: CaseStatus
    to_status: CaseStatus
    actor_id: str
    created_at: str


class _FixedClock:
    timestamp = "2026-08-04T00:00:00Z"

    def now(self) -> str:
        return self.timestamp


class CaseStore:
    def __init__(self) -> None:
        self._clock = _FixedClock()
        self._cases: dict[str, CaseRecord] = {}
        self._timeline: dict[str, list[TimelineEvent]] = {}
        self._applied: dict[str, set[str]] = {}

    def create(
        self,
        *,
        case_id: str,
        actor_id: str,
        payload: dict[str, Any] | None = None,
    ) -> CaseRecord:
        if case_id in self._cases:
            raise DuplicateCaseError(case_id)
        now = self._clock.now()
        record = CaseRecord(
            case_id=case_id,
            status=CaseStatus.CREATED,
            version=1,
            actor_id=actor_id,
            created_at=now,
            updated_at=now,
            payload=dict(payload or {}),
        )
        self._cases[case_id] = record
        self._timeline.setdefault(case_id, [])
        self._applied.setdefault(case_id, set())
        return record

    def get(self, case_id: str) -> CaseRecord | None:
        return self._cases.get(case_id)

    def is_applied(self, case_id: str, command_id: str) -> bool:
        return command_id in self._applied.get(case_id, set())

    def advance(
        self,
        *,
        case_id: str,
        target_status: CaseStatus,
        command_id: str,
        event_type: str,
        actor_id: str,
        payload: dict[str, Any] | None = None,
    ) -> CaseRecord:
        record = self._cases.get(case_id)
        if record is None:
            raise CaseNotFoundError(case_id)
        applied = self._applied.setdefault(case_id, set())
        if command_id in applied:
            return record
        applied.add(command_id)

        now = self._clock.now()
        new_record = CaseRecord(
            case_id=record.case_id,
            status=target_status,
            version=record.version + 1,
            actor_id=actor_id,
            created_at=record.created_at,
            updated_at=now,
            payload=dict(payload or record.payload),
        )
        self._cases[case_id] = new_record
        self._timeline.setdefault(case_id, []).append(
            TimelineEvent(
                event_id=f"evt-{command_id}",
                case_id=case_id,
                command_id=command_id,
                event_type=event_type,
                from_status=record.status,
                to_status=target_status,
                actor_id=actor_id,
                created_at=now,
            )
        )
        return new_record

    def timeline(self, case_id: str) -> list[TimelineEvent]:
        return list(self._timeline.get(case_id, []))
