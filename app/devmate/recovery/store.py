"""devmate 租约存储：owner 排他与副作用幂等去重。"""

from __future__ import annotations

from app.devmate.recovery.types import Lease


class LeaseConflictError(RuntimeError):
    def __init__(self, case_id: str, owner: str) -> None:
        super().__init__(f"active lease held by {owner} for {case_id}")
        self.case_id = case_id
        self.owner = owner


class RecoveryStore:
    def __init__(self) -> None:
        self._leases: dict[str, Lease] = {}
        self._applied: dict[str, set[str]] = {}

    def get_lease(self, case_id: str) -> Lease | None:
        return self._leases.get(case_id)

    def acquire(self, case_id: str, owner: str, now: int, ttl: int) -> Lease:
        current = self._leases.get(case_id)
        if current is not None and current.expires_at >= now:
            raise LeaseConflictError(case_id, current.owner)
        version = (current.version + 1) if current else 1
        lease = Lease(
            case_id=case_id,
            owner=owner,
            acquired_at=now,
            expires_at=now + ttl,
            version=version,
        )
        self._leases[case_id] = lease
        return lease

    def release(self, case_id: str) -> None:
        self._leases.pop(case_id, None)

    def applied(self, case_id: str, side_effect_id: str) -> bool:
        return side_effect_id in self._applied.get(case_id, set())

    def mark_applied(self, case_id: str, side_effect_id: str) -> None:
        self._applied.setdefault(case_id, set()).add(side_effect_id)
