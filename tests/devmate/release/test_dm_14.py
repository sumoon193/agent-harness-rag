"""DevMate DM-14 发布、回滚与真实性审计失败测试。

合同：``RuntimeEvent.execute(input: DM14Input) -> DM14Result``。
发布候选通过回滚演练；未验证项显式保留，不冒充已验证。
"""

from __future__ import annotations

from pathlib import Path

from scripts.devmate.release_kit import (
    DM14Input,
    DM14Result,
    ReleaseCandidate,
    RuntimeEvent,
    UnverifiedItem,
)

SCRIPTS_ROOT = Path(__file__).resolve().parents[3] / "scripts" / "devmate"
DOCS_ROOT = Path(__file__).resolve().parents[3] / "docs" / "devmate" / "release"


def _candidate(
    *,
    candidate_id: str = "rel-1",
    version: str = "1.2.0",
    target_commit: str = "abc123",
    rollback_commit: str = "prev456",
    steps: tuple[str, ...] = ("migrate", "deploy"),
) -> ReleaseCandidate:
    return ReleaseCandidate(
        candidate_id=candidate_id,
        version=version,
        target_commit=target_commit,
        rollback_commit=rollback_commit,
        steps=steps,
    )


def _input(
    *,
    candidate: ReleaseCandidate | None = None,
    unverified: tuple[UnverifiedItem, ...] = (),
) -> DM14Input:
    return DM14Input(candidate=candidate or _candidate(), unverified=unverified)


def test_runtime_event_has_typed_entry() -> None:
    result = RuntimeEvent().execute(_input())

    assert isinstance(result, DM14Result)
    assert result.candidate_id == "rel-1"


def test_candidate_passes_rollback_drill() -> None:
    result = RuntimeEvent().execute(_input())

    assert result.drill.passed is True
    assert result.drill.rolled_back is True


def test_candidate_without_rollback_target_fails_drill() -> None:
    result = RuntimeEvent().execute(
        _input(candidate=_candidate(rollback_commit=""))
    )

    assert result.drill.passed is False
    assert result.drill.rolled_back is False


def test_unverified_items_are_preserved_explicitly() -> None:
    unverified = (
        UnverifiedItem(item="remote branch protection", reason="platform not configured"),
        UnverifiedItem(item="real model", reason="network disabled"),
    )
    result = RuntimeEvent().execute(_input(unverified=unverified))

    assert result.unverified == unverified
    assert result.verified is False
    assert len(result.unverified) == 2


def test_verified_when_drill_passed_and_no_unverified() -> None:
    result = RuntimeEvent().execute(_input())

    assert result.drill.passed is True
    assert result.unverified == ()
    assert result.verified is True


def test_drill_records_each_step() -> None:
    result = RuntimeEvent().execute(_input())

    steps = result.drill.steps
    assert [step[0] for step in steps] == ["migrate", "deploy"]
    assert all(step[1] is True for step in steps)


def test_release_artifacts_exist() -> None:
    scripts = sorted(SCRIPTS_ROOT.glob("*.py"))
    docs = sorted(DOCS_ROOT.glob("*.md"))

    assert scripts, "scripts/devmate must contain a release script"
    assert docs, "docs/devmate/release must contain a release document"
    assert all(path.read_text(encoding="utf-8").strip() for path in scripts + docs)
