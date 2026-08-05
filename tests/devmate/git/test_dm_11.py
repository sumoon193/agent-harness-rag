"""DevMate DM-11 GitHub 副作用与 UNKNOWN 对账失败测试。

合同：``RuntimeEvent.execute(input: DM11Input) -> DM11Result``。
重复发布不重复创建分支/PR；超时副作用进入 UNKNOWN 并可对账。
"""

from __future__ import annotations

from app.devmate.git import (
    DM11Input,
    DM11Result,
    RuntimeEvent,
)


def _input(
    *,
    release_id: str = "rel-1",
    branch: str = "release/rel-1",
    pr_title: str = "Release rel-1",
    timeout: bool = False,
) -> DM11Input:
    return DM11Input(
        release_id=release_id,
        branch=branch,
        pr_title=pr_title,
        timeout=timeout,
    )


def test_runtime_event_has_typed_entry() -> None:
    result = RuntimeEvent().execute(_input())

    assert isinstance(result, DM11Result)
    assert result.effects


def test_release_creates_branch_and_pr_side_effects() -> None:
    result = RuntimeEvent().execute(_input())

    assert len(result.effects) == 2
    kinds = {effect.kind for effect in result.effects}
    assert kinds == {"branch", "pull_request"}
    assert all(effect.status == "created" for effect in result.effects)
    assert result.duplicated is False


def test_duplicate_release_does_not_recreate_side_effects() -> None:
    handler = RuntimeEvent()

    first = handler.execute(_input())
    second = handler.execute(_input())

    assert second.duplicated is True
    assert second.effects == first.effects
    assert len(handler.ledger.effects_for("rel-1")) == 2


def test_timeout_enters_reconciliation() -> None:
    result = RuntimeEvent().execute(_input(timeout=True))

    assert result.reconciliation_required is True
    assert all(effect.status == "unknown" for effect in result.effects)


def test_reconcile_resolves_unknown_effects() -> None:
    handler = RuntimeEvent()
    handler.execute(_input(timeout=True))

    result = handler.reconcile("rel-1")

    assert result.reconciliation_required is False
    assert all(effect.status == "reconciled" for effect in result.effects)


def test_different_releases_create_independent_effects() -> None:
    handler = RuntimeEvent()

    handler.execute(_input(release_id="rel-1"))
    handler.execute(_input(release_id="rel-2"))

    assert len(handler.ledger.effects_for("rel-1")) == 2
    assert len(handler.ledger.effects_for("rel-2")) == 2


def test_effect_carries_audit_fields() -> None:
    result = RuntimeEvent().execute(_input())

    effect = result.effects[0]
    assert effect.effect_id
    assert effect.target
    assert effect.created_at
    assert effect.release_id == "rel-1"
