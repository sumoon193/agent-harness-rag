"""devmate Case 状态机契约。

Case 只能沿 created -> running -> waiting_approval -> completed -> failed
推进，非法转换稳定拒绝。
"""

from __future__ import annotations

from enum import Enum


class CaseStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


LEGAL_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.CREATED: frozenset({CaseStatus.RUNNING}),
    CaseStatus.RUNNING: frozenset({CaseStatus.WAITING_APPROVAL, CaseStatus.FAILED}),
    CaseStatus.WAITING_APPROVAL: frozenset({CaseStatus.COMPLETED, CaseStatus.FAILED}),
    CaseStatus.COMPLETED: frozenset(),
    CaseStatus.FAILED: frozenset(),
}


class IllegalTransitionError(ValueError):
    """非法 Case 状态转换。"""
