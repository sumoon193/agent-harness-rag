"""带 fencing token 的内存运行租约。"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.core.exceptions import ValidationError
from app.schemas.runtime import RunLease
from app.services.runtime.clock import Clock, SystemClock


class InMemoryLeaseStore:
    """防止多个 worker 同时推进同一 Case/Run 的 fallback lease store。"""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._leases: dict[str, RunLease] = {}
        self._tokens: dict[str, int] = {}

    async def acquire(
        self,
        resource_id: str,
        owner_id: str,
        *,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> RunLease:
        """获取或接管已过期租约。"""
        acquired_at = now or self._clock.now()
        current = self._leases.get(resource_id)
        if (
            current is not None
            and current.expires_at > acquired_at
            and current.owner_id != owner_id
        ):
            raise ValidationError(
                f"Resource already leased: {resource_id} by {current.owner_id}"
            )

        token = self._tokens.get(resource_id, 0) + 1
        lease = RunLease(
            resource_id=resource_id,
            owner_id=owner_id,
            acquired_at=acquired_at,
            expires_at=acquired_at + timedelta(seconds=ttl_seconds),
            fencing_token=token,
        )
        self._leases[resource_id] = lease
        self._tokens[resource_id] = token
        return lease.model_copy(deep=True)

    async def release(
        self,
        resource_id: str,
        owner_id: str,
        fencing_token: int,
    ) -> None:
        """仅允许当前 owner 使用最新 fencing token 释放租约。"""
        current = self._leases.get(resource_id)
        if current is None:
            return
        if current.owner_id != owner_id or current.fencing_token != fencing_token:
            raise ValidationError(f"Lease owner or fencing token mismatch: {resource_id}")
        del self._leases[resource_id]
