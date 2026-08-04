"""devmate Webhook 摄取存储：以 webhook_id 幂等去重。"""

from __future__ import annotations

from app.devmate.ingestion.models import EvidenceBundle


class InvalidWebhookError(ValueError):
    """webhook 输入非法。"""


class IngestionStore:
    """追加式证据存储；重复 webhook_id 返回既有证据，不覆盖。"""

    def __init__(self) -> None:
        self._by_webhook: dict[str, EvidenceBundle] = {}
        self._by_evidence: dict[str, EvidenceBundle] = {}

    def ingest(self, bundle: EvidenceBundle) -> tuple[EvidenceBundle, bool]:
        prior = self._by_webhook.get(bundle.webhook_id)
        if prior is not None:
            return prior, True
        self._by_webhook[bundle.webhook_id] = bundle
        self._by_evidence[bundle.evidence_id] = bundle
        return bundle, False

    def evidence_by_webhook(self) -> dict[str, EvidenceBundle]:
        return dict(self._by_webhook)

    def evidence(self, evidence_id: str) -> EvidenceBundle | None:
        return self._by_evidence.get(evidence_id)
