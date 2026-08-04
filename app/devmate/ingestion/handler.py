"""devmate Webhook 摄取 typed 入口。

合同：``RuntimeEvent.execute(input: DM05Input) -> DM05Result``。
重复 webhook 以 webhook_id 幂等；commit/CI evidence 固定不可变。
"""

from __future__ import annotations

from app.devmate.ingestion.models import (
    DM05Input,
    DM05Result,
    EvidenceBundle,
    _payload_hash,
)
from app.devmate.ingestion.store import IngestionStore, InvalidWebhookError


class RuntimeEvent:
    def __init__(self, store: IngestionStore | None = None) -> None:
        self.store = store or IngestionStore()

    def execute(self, input_: DM05Input) -> DM05Result:
        _validate(input_)
        bundle = EvidenceBundle(
            evidence_id=f"ev-{input_.webhook_id}",
            webhook_id=input_.webhook_id,
            source=input_.source,
            event_type=input_.event_type,
            commit=input_.commit,
            ci=input_.ci,
            payload_hash=_payload_hash(input_.payload),
            received_at=input_.received_at,
        )
        stored, duplicate = self.store.ingest(bundle)
        return DM05Result(
            webhook_id=stored.webhook_id,
            evidence_id=stored.evidence_id,
            duplicate=duplicate,
            source=stored.source,
            event_type=stored.event_type,
            evidence=stored,
        )


def _validate(input_: DM05Input) -> None:
    if not input_.webhook_id or not input_.webhook_id.strip():
        raise InvalidWebhookError("webhook_id is required")
    if not input_.source or not input_.source.strip():
        raise InvalidWebhookError("source is required")
    if not input_.event_type or not input_.event_type.strip():
        raise InvalidWebhookError("event_type is required")
    if input_.commit is not None and not input_.commit.commit_sha:
        raise InvalidWebhookError("commit evidence requires commit_sha")
    if input_.ci is not None and not input_.ci.ci_run_id:
        raise InvalidWebhookError("ci evidence requires ci_run_id")
