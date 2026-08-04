"""DevMate DM-03 Event Store、Projection 与 Outbox 失败测试。

合同：``CheckpointPort.execute(input: DM03Input) -> DM03Result``。
事件与 Outbox 消息在同一 Checkpoint 事务内原子提交，版本冲突时不产生
任何写入；Projection 可从事件流重建；devmate_case 记录携带主键、版本/
幂等键、创建更新时间与审计来源。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.devmate.runtime import DM03Input, DM03Result, TransactionalCheckpoint
from app.devmate.runtime.event_store import ConcurrentVersionError, EventStore
from app.devmate.runtime.outbox import Outbox
from app.devmate.runtime.projection import Projection

MIGRATIONS_ROOT = Path(__file__).resolve().parents[3] / "migrations" / "devmate"

REQUIRED_MIGRATION_FIELDS = (
    "case_id",
    "version",
    "checkpoint_id",
    "created_at",
    "updated_at",
    "audit_source",
)


def _input(
    *,
    checkpoint_id: str = "cp-1",
    aggregate_id: str = "case-1",
    event_type: str = "case.created",
    payload: dict[str, object] | None = None,
    expected_version: int = 0,
    actor_id: str = "u-1",
    status: str = "created",
    outbox_topics: tuple[str, ...] = ("github",),
) -> DM03Input:
    return DM03Input(
        checkpoint_id=checkpoint_id,
        aggregate_id=aggregate_id,
        aggregate_type="devmate_case",
        event_type=event_type,
        payload=payload or {},
        expected_version=expected_version,
        actor_id=actor_id,
        status=status,
        outbox_topics=outbox_topics,
    )


def _port() -> tuple[TransactionalCheckpoint, EventStore, Outbox]:
    store = EventStore()
    outbox = Outbox()
    port = TransactionalCheckpoint(store=store, outbox=outbox, projection=Projection())
    return port, store, outbox


def test_checkpoint_port_has_typed_entry() -> None:
    port, _, _ = _port()

    result = port.execute(_input())

    assert isinstance(result, DM03Result)
    assert result.checkpoint_id == "cp-1"
    assert result.new_version == 1
    assert result.outbox_ids


def test_event_and_outbox_commit_in_same_transaction() -> None:
    port, store, outbox = _port()

    port.execute(_input(checkpoint_id="cp-1"))

    assert store.size() == 1
    assert outbox.size() == 1
    stream = store.load_stream("case-1")
    assert stream[0].version == 1
    assert stream[0].event_type == "case.created"
    assert outbox.unread()[0].topic == "github"


def test_version_conflict_aborts_event_and_outbox_atomically() -> None:
    port, store, outbox = _port()
    port.execute(_input(checkpoint_id="cp-1", expected_version=0))

    with pytest.raises(ConcurrentVersionError):
        port.execute(_input(checkpoint_id="cp-2", expected_version=0))

    assert store.size() == 1  # 事件未被写入
    assert outbox.size() == 1  # Outbox 未被写入
    assert len(store.load_stream("case-1")) == 1


def test_checkpoint_is_idempotent_by_checkpoint_id() -> None:
    port, store, outbox = _port()

    first = port.execute(_input(checkpoint_id="cp-1"))
    second = port.execute(_input(checkpoint_id="cp-1"))

    assert first == second
    assert store.size() == 1
    assert outbox.size() == 1


def test_event_stream_is_versioned_append_only() -> None:
    port, store, _ = _port()

    port.execute(
        _input(checkpoint_id="cp-1", event_type="case.created", expected_version=0)
    )
    port.execute(
        _input(checkpoint_id="cp-2", event_type="case.started", expected_version=1)
    )

    stream = store.load_stream("case-1")
    assert [event.version for event in stream] == [1, 2]
    assert [event.event_type for event in stream] == ["case.created", "case.started"]


def test_projection_is_rebuildable_from_event_stream() -> None:
    port, store, _ = _port()

    first = port.execute(
        _input(checkpoint_id="cp-1", event_type="case.created", expected_version=0)
    )
    second = port.execute(
        _input(checkpoint_id="cp-2", event_type="case.started", expected_version=1)
    )

    rebuilt = Projection().rebuild(store.all_events())

    assert rebuilt == second.projection
    assert first.projection["case-1"]["event_count"] == 1
    assert rebuilt["case-1"]["event_count"] == 2
    assert rebuilt["case-1"]["types"] == ["case.created", "case.started"]


def test_case_record_carries_audit_fields() -> None:
    port, _, _ = _port()

    port.execute(
        _input(checkpoint_id="cp-1", event_type="case.created", actor_id="u-7")
    )

    record = port.case_records()["case-1"]
    assert record.case_id == "case-1"
    assert record.version == 1
    assert record.checkpoint_id == "cp-1"
    assert record.audit_source == "u-7"
    assert record.created_at
    assert record.updated_at


def test_outbox_messages_are_ordered_and_per_topic() -> None:
    port, _, outbox = _port()

    port.execute(_input(checkpoint_id="cp-1", outbox_topics=("github", "notify")))

    messages = outbox.unread()
    assert [message.topic for message in messages] == ["github", "notify"]
    assert messages[0].checkpoint_id == "cp-1"


def test_migration_declares_devmate_case_with_required_fields() -> None:
    sql_files = sorted(MIGRATIONS_ROOT.glob("*.sql"))
    assert sql_files, "migrations/devmate must contain a SQL migration"
    ddl = "\n".join(path.read_text(encoding="utf-8") for path in sql_files).lower()
    assert "primary key" in ddl
    for field in REQUIRED_MIGRATION_FIELDS:
        assert field in ddl, f"migration missing required field: {field}"
