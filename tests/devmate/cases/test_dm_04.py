"""DevMate DM-04 Case 状态机失败测试。

合同：``CaseCommand.execute(input: DM04Input) -> DM04Result``。
Case 只能沿 created -> running -> waiting_approval -> completed -> failed
推进，非法转换稳定拒绝；command_id 幂等；timeline 记录审计信息。
"""

from __future__ import annotations

import pytest

from app.devmate.cases import (
    CaseCommand,
    CaseNotFoundError,
    CaseStatus,
    CaseStore,
    DM04Input,
    DM04Result,
    DuplicateCaseError,
    IllegalTransitionError,
)


def _store() -> CaseStore:
    return CaseStore()


def _setup(store: CaseStore, *, case_id: str = "case-1", actor_id: str = "u-1") -> None:
    store.create(case_id=case_id, actor_id=actor_id, payload={"subject": "s1"})


def _input(
    *,
    case_id: str = "case-1",
    command_id: str = "cmd-1",
    event_type: str = "case.start",
    actor_id: str = "u-1",
    target_status: CaseStatus = CaseStatus.RUNNING,
    payload: dict[str, object] | None = None,
) -> DM04Input:
    return DM04Input(
        case_id=case_id,
        command_id=command_id,
        event_type=event_type,
        actor_id=actor_id,
        target_status=target_status,
        payload=payload or {},
    )


def test_case_command_has_typed_entry() -> None:
    store = _store()
    _setup(store)

    result = CaseCommand(store).execute(_input())

    assert isinstance(result, DM04Result)
    assert result.case_id == "case-1"
    assert result.status is CaseStatus.RUNNING


def test_legal_state_machine_path_via_commands() -> None:
    store = _store()
    _setup(store)
    command = CaseCommand(store)

    current = CaseStatus.CREATED
    for index, target in enumerate(
        (CaseStatus.RUNNING, CaseStatus.WAITING_APPROVAL, CaseStatus.COMPLETED),
        start=1,
    ):
        result = command.execute(_input(command_id=f"cmd-{index}", target_status=target))
        assert result.status is target
        current = result.status
    assert current is CaseStatus.COMPLETED


def test_illegal_transition_is_stably_rejected() -> None:
    store = _store()
    _setup(store)

    with pytest.raises(IllegalTransitionError):
        CaseCommand(store).execute(_input(target_status=CaseStatus.COMPLETED))


def test_unknown_case_is_rejected() -> None:
    store = _store()

    with pytest.raises(CaseNotFoundError):
        CaseCommand(store).execute(_input(case_id="missing"))


def test_command_is_idempotent_by_command_id() -> None:
    store = _store()
    _setup(store)
    command = CaseCommand(store)

    first = command.execute(_input(command_id="cmd-1"))
    second = command.execute(_input(command_id="cmd-1"))

    assert first == second
    assert len(store.timeline("case-1")) == 1


def test_timeline_records_transitions_with_audit() -> None:
    store = _store()
    _setup(store, actor_id="u-9")

    CaseCommand(store).execute(_input(command_id="cmd-1", actor_id="u-9"))

    events = store.timeline("case-1")
    assert len(events) == 1
    assert events[0].from_status is CaseStatus.CREATED
    assert events[0].to_status is CaseStatus.RUNNING
    assert events[0].actor_id == "u-9"
    assert events[0].command_id == "cmd-1"


def test_duplicate_case_creation_is_rejected() -> None:
    store = _store()
    _setup(store)

    with pytest.raises(DuplicateCaseError):
        store.create(case_id="case-1", actor_id="u-2", payload={})
