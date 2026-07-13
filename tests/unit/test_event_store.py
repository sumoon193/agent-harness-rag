"""Agent Runtime Event Store 单元测试。"""
from __future__ import annotations

import pytest

from app.services.runtime.event_store import InMemoryEventStore


@pytest.mark.asyncio
async def test_append_assigns_monotonic_sequence_and_hash_chain() -> None:
    """同一聚合的事件应按顺序追加并形成可校验哈希链。"""
    store = InMemoryEventStore()

    created = await store.append(
        aggregate_id="case_001",
        aggregate_type="hr_case",
        event_type="case.created",
        payload={"title": "新员工入职到转正"},
        command_id="cmd_create",
        expected_version=0,
        actor_id="user_001",
    )
    message = await store.append(
        aggregate_id="case_001",
        aggregate_type="hr_case",
        event_type="case.message_added",
        payload={"message": "我已提交入职材料"},
        command_id="cmd_message",
        expected_version=1,
        actor_id="user_001",
    )

    assert [created.sequence, message.sequence] == [1, 2]
    assert created.prev_hash == ""
    assert message.prev_hash == created.event_hash
    assert await store.verify_chain("case_001") is True


@pytest.mark.asyncio
async def test_append_with_duplicate_command_returns_original_event() -> None:
    """同一命令重放时不应产生重复领域事件。"""
    store = InMemoryEventStore()
    values = {
        "aggregate_id": "case_001",
        "aggregate_type": "hr_case",
        "event_type": "case.created",
        "payload": {"title": "新员工入职到转正"},
        "command_id": "cmd_create",
        "expected_version": 0,
        "actor_id": "user_001",
    }

    first = await store.append(**values)
    replayed = await store.append(**values)

    assert replayed.id == first.id
    assert len(await store.load_stream("case_001")) == 1


@pytest.mark.asyncio
async def test_append_creates_outbox_message_that_can_be_acknowledged() -> None:
    """事件追加应同时产生可幂等投递的 outbox message。"""
    store = InMemoryEventStore()

    event = await store.append(
        aggregate_id="case_001",
        aggregate_type="hr_case",
        event_type="case.created",
        payload={"title": "新员工入职到转正"},
        command_id="cmd_create",
        expected_version=0,
        actor_id="user_001",
    )

    pending = await store.pending_outbox()
    assert len(pending) == 1
    assert pending[0].event_id == event.id
    claimed = await store.claim_outbox(owner_id="publisher_a", limit=10)
    assert claimed[0].id == pending[0].id
    await store.mark_outbox_published(pending[0].id, owner_id="publisher_a")
    assert await store.pending_outbox() == []
