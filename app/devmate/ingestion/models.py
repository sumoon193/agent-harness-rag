"""devmate Webhook 摄取领域模型。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommitEvidence:
    commit_sha: str
    branch: str
    repo: str


@dataclass(frozen=True)
class CIEvidence:
    ci_run_id: str
    ci_status: str
    ci_url: str | None = None


@dataclass(frozen=True)
class EvidenceBundle:
    evidence_id: str
    webhook_id: str
    source: str
    event_type: str
    commit: CommitEvidence | None
    ci: CIEvidence | None
    payload_hash: str
    received_at: str


@dataclass(frozen=True)
class DM05Input:
    webhook_id: str
    source: str
    event_type: str
    payload: dict[str, Any]
    commit: CommitEvidence | None = None
    ci: CIEvidence | None = None
    received_at: str = "2026-08-04T00:00:00Z"


@dataclass(frozen=True)
class DM05Result:
    webhook_id: str
    evidence_id: str
    duplicate: bool
    source: str
    event_type: str
    evidence: EvidenceBundle


def _payload_hash(payload: dict[str, Any]) -> str:
    """确定性指纹：排序键 JSON 后 SHA-256。"""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
