"""DevMate DM-01 来源、许可证与 origin audit 的 typed command 入口。

实现合同 ``CaseCommand.execute(input: DM01Input) -> DM01Result``：缺少来源
提交（untracked）或许可证（unknown/unconfirmed/conflict/review）的文件保持
review/blocked，Case 只能沿 created -> running -> waiting_approval ->
completed -> failed 推进，非法转换稳定拒绝，未通过审计的文件不能进入
completed。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CaseStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class FileAuditStatus(str, Enum):
    OK = "ok"
    REVIEW = "review"
    BLOCKED = "blocked"


MISSING_LICENSE_STATUSES = frozenset(
    {"unknown", "unconfirmed", "conflict", "review"}
)

# 合法状态机：created -> running -> waiting_approval -> completed / failed。
LEGAL_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.CREATED: frozenset({CaseStatus.RUNNING}),
    CaseStatus.RUNNING: frozenset(
        {CaseStatus.WAITING_APPROVAL, CaseStatus.FAILED}
    ),
    CaseStatus.WAITING_APPROVAL: frozenset(
        {CaseStatus.COMPLETED, CaseStatus.FAILED}
    ),
    CaseStatus.COMPLETED: frozenset(),
    CaseStatus.FAILED: frozenset(),
}


class IllegalTransitionError(ValueError):
    """非法 Case 状态转换或未通过审计文件的完成尝试。"""


def classify_file_audit(source_commit: str, license_status: str) -> FileAuditStatus:
    """缺少来源或许可证 -> review/blocked；来源与许可证齐全才 ok。"""
    if license_status == "conflict":
        return FileAuditStatus.BLOCKED
    if source_commit in {"", "untracked"} or license_status in MISSING_LICENSE_STATUSES:
        return FileAuditStatus.REVIEW
    return FileAuditStatus.OK


@dataclass(frozen=True)
class DM01Input:
    case_id: str
    file_path: str
    source_commit: str
    license_status: str
    current_status: CaseStatus = CaseStatus.CREATED
    target_status: CaseStatus = CaseStatus.RUNNING


@dataclass(frozen=True)
class DM01Result:
    case_id: str
    status: CaseStatus
    file_audit_status: FileAuditStatus
    state_event: str
    audit_info: dict[str, str]
    transitioned: bool


class CaseCommand:
    """来源、许可证与 origin audit 的 typed command。"""

    @staticmethod
    def execute(input_: DM01Input) -> DM01Result:
        if input_.target_status not in LEGAL_TRANSITIONS[input_.current_status]:
            raise IllegalTransitionError(
                "illegal transition "
                f"{input_.current_status.value} -> {input_.target_status.value}"
            )

        file_audit_status = classify_file_audit(
            input_.source_commit,
            input_.license_status,
        )
        if (
            input_.target_status is CaseStatus.COMPLETED
            and file_audit_status is not FileAuditStatus.OK
        ):
            raise IllegalTransitionError(
                "file missing provenance or license cannot complete: "
                f"{input_.file_path} ({file_audit_status.value})"
            )

        return DM01Result(
            case_id=input_.case_id,
            status=input_.target_status,
            file_audit_status=file_audit_status,
            state_event=(
                f"case {input_.case_id} {input_.current_status.value}"
                f" -> {input_.target_status.value}"
            ),
            audit_info={
                "source_commit": input_.source_commit,
                "license_status": input_.license_status,
                "file_audit_status": file_audit_status.value,
            },
            transitioned=True,
        )
