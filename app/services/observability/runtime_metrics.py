"""Agent Runtime 工程指标的线程安全 fallback collector。"""
from __future__ import annotations

from collections import defaultdict
from threading import Lock

from app.schemas.runtime import RuntimeMetricsSnapshot
from app.services.runtime.clock import Clock, SystemClock


class RuntimeMetrics:
    """记录 counters、gauges 和 observations，可由 OTel adapter 导出。"""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._counters: dict[str, int] = defaultdict(int)
        for name in (
            "runtime.cases.started",
            "runtime.cases.completed",
            "runtime.approvals.requested",
            "runtime.approvals.decided",
            "runtime.human_interventions.total",
            "runtime.side_effects.succeeded",
            "runtime.side_effects.duplicate",
            "runtime.unsafe_tool_execution.total",
            "runtime.approval_bypass.total",
            "runtime.acl_violations.total",
            "runtime.evidence.stale",
            "runtime.context.invariant_failures",
            "runtime.crash_recovery.success",
            "runtime.protocol.mcp.success",
            "runtime.protocol.a2a.success",
            "runtime.protocol_failures.mcp",
            "runtime.protocol_failures.a2a",
            "runtime.repairs.total",
            "runtime.budget_exhausted.total",
        ):
            self._counters[name] = 0
        self._gauges: dict[str, float] = {}
        self._observations: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def increment(self, name: str, value: int = 1) -> None:
        """增加单调 counter。"""
        with self._lock:
            self._counters[name] += value

    def set_gauge(self, name: str, value: int | float) -> None:
        """设置当前 gauge。"""
        with self._lock:
            self._gauges[name] = float(value)

    def observe(self, name: str, value: int | float) -> None:
        """记录 histogram/summary 原始观测值。"""
        with self._lock:
            self._observations[name].append(float(value))

    def snapshot(self) -> RuntimeMetricsSnapshot:
        """返回不可变数据副本。"""
        with self._lock:
            return RuntimeMetricsSnapshot(
                counters=dict(self._counters),
                gauges=dict(self._gauges),
                observations={
                    key: list(values) for key, values in self._observations.items()
                },
                generated_at=self._clock.now(),
            )
