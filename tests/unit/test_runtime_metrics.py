"""Agent Runtime 工程指标测试。"""
from __future__ import annotations

import pytest

from app.services.observability.runtime_metrics import RuntimeMetrics
from app.services.runtime.event_store import InMemoryEventStore


@pytest.mark.asyncio
async def test_event_store_updates_event_and_outbox_metrics() -> None:
    """事件追加与 outbox ack 应自动更新核心运行指标。"""
    metrics = RuntimeMetrics()
    store = InMemoryEventStore(metrics=metrics)

    for version in range(2):
        await store.append(
            aggregate_id="case_001",
            aggregate_type="hr_case",
            event_type="case.updated",
            payload={"version": version + 1},
            command_id=f"cmd_{version}",
            expected_version=version,
            actor_id="user_hr",
        )
    first_outbox = (await store.claim_outbox(owner_id="publisher_a", limit=1))[0]
    await store.mark_outbox_published(first_outbox.id, owner_id="publisher_a")
    snapshot = metrics.snapshot()

    assert snapshot.counters["runtime.events.total"] == 2
    assert snapshot.counters["runtime.outbox.published"] == 1
    assert snapshot.gauges["runtime.outbox.backlog"] == 1.0


def test_runtime_metrics_tracks_agent_governance_signals() -> None:
    """指标器应记录 projection、审批、修复、协议和预算信号。"""
    metrics = RuntimeMetrics()
    metrics.observe("runtime.projection.lag_ms", 120.0)
    metrics.set_gauge("runtime.approvals.stuck", 2)
    metrics.increment("runtime.repairs.total")
    metrics.increment("runtime.protocol_failures.mcp")
    metrics.increment("runtime.budget_exhausted.total")

    snapshot = metrics.snapshot()
    assert snapshot.observations["runtime.projection.lag_ms"] == [120.0]
    assert snapshot.gauges["runtime.approvals.stuck"] == 2.0
    assert snapshot.counters["runtime.repairs.total"] == 1
    assert snapshot.counters["runtime.protocol_failures.mcp"] == 1
    assert snapshot.counters["runtime.budget_exhausted.total"] == 1
