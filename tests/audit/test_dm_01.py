"""DevMate DM-01 来源、许可证与 origin audit 失败测试。

合同：``CaseCommand.execute(input: DM01Input) -> DM01Result``。
缺少来源提交（untracked）或许可证（unknown/unconfirmed/conflict/review）的
文件保持 review/blocked，Case 只能沿
created -> running -> waiting_approval -> completed -> failed 推进，
非法转换稳定拒绝，未通过审计的文件不能进入 completed。
"""

from __future__ import annotations

import pytest

from scripts.audit_case_command import (
    CaseCommand,
    CaseStatus,
    DM01Input,
    DM01Result,
    FileAuditStatus,
    IllegalTransitionError,
    classify_file_audit,
)


def _input(
    *,
    file_path: str = "app/example.py",
    source_commit: str = "a" * 40,
    license_status: str = "confirmed",
    current_status: CaseStatus = CaseStatus.CREATED,
    target_status: CaseStatus = CaseStatus.RUNNING,
) -> DM01Input:
    return DM01Input(
        case_id="case-1",
        file_path=file_path,
        source_commit=source_commit,
        license_status=license_status,
        current_status=current_status,
        target_status=target_status,
    )


def test_dm01_has_typed_command_entry() -> None:
    result = CaseCommand.execute(_input())

    assert isinstance(result, DM01Result)
    assert result.case_id == "case-1"
    assert result.status is CaseStatus.RUNNING
    assert result.transitioned is True


def test_ok_file_with_provenance_and_license_is_ok() -> None:
    assert classify_file_audit("a" * 40, "confirmed") is FileAuditStatus.OK


def test_missing_provenance_stays_review_or_blocked() -> None:
    result = CaseCommand.execute(
        _input(source_commit="untracked", license_status="confirmed")
    )

    assert result.file_audit_status is not FileAuditStatus.OK
    assert result.file_audit_status in {
        FileAuditStatus.REVIEW,
        FileAuditStatus.BLOCKED,
    }


def test_missing_license_stays_review_or_blocked() -> None:
    for license_status in ("unknown", "unconfirmed", "conflict", "review"):
        result = CaseCommand.execute(_input(license_status=license_status))
        assert result.file_audit_status in {
            FileAuditStatus.REVIEW,
            FileAuditStatus.BLOCKED,
        }, license_status


def test_conflict_license_is_blocked() -> None:
    assert classify_file_audit("a" * 40, "conflict") is FileAuditStatus.BLOCKED


def test_legal_state_machine_path_completes() -> None:
    current = CaseStatus.CREATED
    for target in (
        CaseStatus.RUNNING,
        CaseStatus.WAITING_APPROVAL,
        CaseStatus.COMPLETED,
    ):
        result = CaseCommand.execute(
            _input(current_status=current, target_status=target)
        )
        assert result.transitioned is True
        current = result.status
    assert current is CaseStatus.COMPLETED


def test_failed_is_reachable_from_running_and_waiting_approval() -> None:
    for current in (CaseStatus.RUNNING, CaseStatus.WAITING_APPROVAL):
        result = CaseCommand.execute(
            _input(current_status=current, target_status=CaseStatus.FAILED)
        )
        assert result.status is CaseStatus.FAILED


def test_illegal_transition_is_stably_rejected() -> None:
    with pytest.raises(IllegalTransitionError):
        CaseCommand.execute(
            _input(current_status=CaseStatus.CREATED, target_status=CaseStatus.COMPLETED)
        )
    with pytest.raises(IllegalTransitionError):
        CaseCommand.execute(
            _input(current_status=CaseStatus.RUNNING, target_status=CaseStatus.CREATED)
        )
    with pytest.raises(IllegalTransitionError):
        CaseCommand.execute(
            _input(current_status=CaseStatus.COMPLETED, target_status=CaseStatus.RUNNING)
        )


def test_review_blocked_file_cannot_complete() -> None:
    with pytest.raises(IllegalTransitionError):
        CaseCommand.execute(
            _input(
                source_commit="untracked",
                license_status="confirmed",
                current_status=CaseStatus.WAITING_APPROVAL,
                target_status=CaseStatus.COMPLETED,
            )
        )
    with pytest.raises(IllegalTransitionError):
        CaseCommand.execute(
            _input(
                source_commit="a" * 40,
                license_status="unknown",
                current_status=CaseStatus.WAITING_APPROVAL,
                target_status=CaseStatus.COMPLETED,
            )
        )


def test_result_carries_state_event_and_audit_info() -> None:
    result = CaseCommand.execute(
        _input(source_commit="a" * 40, license_status="confirmed")
    )

    assert result.state_event
    assert "created" in result.state_event
    assert result.audit_info["source_commit"] == "a" * 40
    assert result.audit_info["license_status"] == "confirmed"
