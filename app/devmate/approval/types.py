"""devmate 审批领域类型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    case_id: str
    patch_id: str
    evidence_ids: tuple[str, ...]
    command: str
    requested_by: str
    requested_at: str = "2026-08-04T00:00:00Z"
    expires_at: str = "2026-08-04T23:59:59Z"
    status: str = "pending"
    decided_by: str = ""


@dataclass(frozen=True)
class DM10Input:
    approval_id: str
    decision: str
    decided_by: str
    decided_at: str


@dataclass(frozen=True)
class DM10Result:
    approval_id: str
    case_id: str
    patch_id: str
    evidence_ids: tuple[str, ...]
    command: str
    decided_by: str
    status: str
    expires_at: str
    audit: dict[str, str]
