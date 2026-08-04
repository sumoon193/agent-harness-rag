"""DevMate DM-05 Webhook 与 evidence 摄取失败测试。

合同：``RuntimeEvent.execute(input: DM05Input) -> DM05Result``。
重复 webhook 以 webhook_id 幂等，不重复摄取；commit/CI evidence 固定
不可变，携带可复核来源。
"""

from __future__ import annotations

import pytest

from app.devmate.ingestion import (
    CIEvidence,
    CommitEvidence,
    DM05Input,
    DM05Result,
    EvidenceBundle,
    InvalidWebhookError,
    RuntimeEvent,
)


def _input(
    *,
    webhook_id: str = "wh-1",
    source: str = "github",
    event_type: str = "push",
    payload: dict[str, object] | None = None,
    commit: CommitEvidence | None = None,
    ci: CIEvidence | None = None,
) -> DM05Input:
    return DM05Input(
        webhook_id=webhook_id,
        source=source,
        event_type=event_type,
        payload=payload or {"head_commit": "abc"},
        commit=commit or CommitEvidence(
            commit_sha="abc123", branch="main", repo="org/repo"
        ),
        ci=ci or CIEvidence(ci_run_id="ci-9", ci_status="success"),
    )


def test_runtime_event_has_typed_entry() -> None:
    result = RuntimeEvent().execute(_input())

    assert isinstance(result, DM05Result)
    assert result.webhook_id == "wh-1"
    assert result.duplicate is False
    assert result.evidence_id


def test_duplicate_webhook_is_idempotent() -> None:
    handler = RuntimeEvent()

    first = handler.execute(_input(webhook_id="wh-1"))
    second = handler.execute(_input(webhook_id="wh-1"))

    assert second.duplicate is True
    assert second.evidence_id == first.evidence_id
    assert second.evidence == first.evidence
    assert len(handler.store.evidence_by_webhook()) == 1


def test_duplicate_with_different_payload_returns_prior_result() -> None:
    handler = RuntimeEvent()

    first = handler.execute(_input(webhook_id="wh-1", payload={"head_commit": "abc"}))
    second = handler.execute(
        _input(webhook_id="wh-1", payload={"head_commit": "changed"})
    )

    assert second.evidence == first.evidence
    assert second.evidence.payload_hash == first.evidence.payload_hash


def test_commit_and_ci_evidence_are_fixed() -> None:
    handler = RuntimeEvent()

    result = handler.execute(_input())

    evidence: EvidenceBundle = result.evidence
    assert evidence.commit.commit_sha == "abc123"
    assert evidence.commit.branch == "main"
    assert evidence.ci.ci_run_id == "ci-9"
    assert evidence.ci.ci_status == "success"
    assert evidence.payload_hash
    assert evidence.received_at


def test_evidence_is_immutable_and_retrievable() -> None:
    handler = RuntimeEvent()
    result = handler.execute(_input(webhook_id="wh-1"))

    stored = handler.store.evidence(result.evidence_id)
    assert stored == result.evidence


def test_invalid_webhook_is_stably_rejected() -> None:
    handler = RuntimeEvent()

    with pytest.raises(InvalidWebhookError):
        handler.execute(_input(webhook_id=""))


def test_multiple_distinct_webhooks_are_kept() -> None:
    handler = RuntimeEvent()

    handler.execute(_input(webhook_id="wh-1"))
    handler.execute(_input(webhook_id="wh-2", event_type="pull_request"))

    assert len(handler.store.evidence_by_webhook()) == 2
