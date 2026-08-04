"""DevMate DM-02 领域隔离与端口合同失败测试。

合同：``RuntimeEvent.execute(input: DM02Input) -> DM02Result``。
``app/devmate/contracts/`` 端口契约是 Runtime 候选的依赖边界，不引用
HR/RAG 领域接口；Case 状态机
created -> running -> waiting_approval -> completed -> failed 非法转换
稳定拒绝。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.devmate.contracts.commands import DM02Input, DM02Result, RuntimeEvent
from app.devmate.contracts.ports import (
    CaseRecord,
    CaseStorePort,
    ClockPort,
    EventStreamPort,
)
from app.devmate.contracts.state import CaseStatus, IllegalTransitionError

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[3] / "app" / "devmate" / "contracts"
)

# HR/RAG 领域接口标识符：契约层不得出现。
HR_RAG_DOMAIN_TOKENS = (
    r"\bHRCase\b",
    r"\bhr_case\b",
    r"\bhr_policy\b",
    r"\bOnboardingCaseWorkflow\b",
    r"\bexpense\b",
    r"\bleave\b",
    r"\bregularization\b",
    r"\bEvidenceBundle\b",
    r"\bembedding\b",
    r"\bretrieval\b",
    r"\bapp\.prompts\b",
    r"\bFastAPI\b",
    r"\bAPIRouter\b",
)


def _input(
    *,
    runtime_id: str = "rt-1",
    event_type: str = "tick",
    payload: dict[str, object] | None = None,
    current_status: CaseStatus = CaseStatus.CREATED,
    target_status: CaseStatus = CaseStatus.RUNNING,
) -> DM02Input:
    return DM02Input(
        runtime_id=runtime_id,
        event_type=event_type,
        payload=payload or {},
        current_status=current_status,
        target_status=target_status,
    )


def test_runtime_event_has_typed_entry() -> None:
    result = RuntimeEvent.execute(_input())

    assert isinstance(result, DM02Result)
    assert result.runtime_id == "rt-1"
    assert result.status is CaseStatus.RUNNING


def test_legal_state_machine_path_completes() -> None:
    current = CaseStatus.CREATED
    for target in (
        CaseStatus.RUNNING,
        CaseStatus.WAITING_APPROVAL,
        CaseStatus.COMPLETED,
    ):
        result = RuntimeEvent.execute(
            _input(current_status=current, target_status=target)
        )
        assert result.status is target
        current = result.status
    assert current is CaseStatus.COMPLETED


def test_failed_reachable_from_running_and_waiting_approval() -> None:
    for current in (CaseStatus.RUNNING, CaseStatus.WAITING_APPROVAL):
        result = RuntimeEvent.execute(
            _input(current_status=current, target_status=CaseStatus.FAILED)
        )
        assert result.status is CaseStatus.FAILED


def test_illegal_transition_is_stably_rejected() -> None:
    for current, target in (
        (CaseStatus.CREATED, CaseStatus.COMPLETED),
        (CaseStatus.RUNNING, CaseStatus.CREATED),
        (CaseStatus.COMPLETED, CaseStatus.RUNNING),
        (CaseStatus.FAILED, CaseStatus.RUNNING),
    ):
        with pytest.raises(IllegalTransitionError):
            RuntimeEvent.execute(
                _input(current_status=current, target_status=target)
            )


def test_result_carries_state_event_and_audit_info() -> None:
    result = RuntimeEvent.execute(
        _input(event_type="case.start", payload={"actor": "u1"})
    )

    assert result.state_event
    assert "created" in result.state_event
    assert result.audit_info["event_type"] == "case.start"


def test_ports_expose_neutral_contract_methods() -> None:
    assert hasattr(EventStreamPort, "append")
    assert hasattr(EventStreamPort, "load_stream")
    assert hasattr(CaseStorePort, "get")
    assert hasattr(CaseStorePort, "upsert")
    assert hasattr(ClockPort, "now")
    assert CaseRecord.__dataclass_fields__["case_id"]


def test_contracts_do_not_reference_hr_rag_domain_interfaces() -> None:
    patterns = [re.compile(token) for token in HR_RAG_DOMAIN_TOKENS]
    sources = sorted(CONTRACTS_ROOT.rglob("*.py"))
    assert sources, "contracts package must contain Python sources"
    for source_path in sources:
        source = source_path.read_text(encoding="utf-8")
        for pattern in patterns:
            assert pattern.search(source) is None, (
                f"{source_path.relative_to(CONTRACTS_ROOT)} hits "
                f"{pattern.pattern}"
            )
