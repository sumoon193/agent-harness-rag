"""devmate 发布、回滚与真实性审计核心逻辑（位于 scripts 白名单内）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReleaseCandidate:
    candidate_id: str
    version: str
    target_commit: str
    rollback_commit: str
    steps: tuple[str, ...]


@dataclass(frozen=True)
class UnverifiedItem:
    item: str
    reason: str


@dataclass(frozen=True)
class RollbackDrillResult:
    passed: bool
    steps: tuple[tuple[str, bool], ...]
    rolled_back: bool


@dataclass(frozen=True)
class DM14Input:
    candidate: ReleaseCandidate
    unverified: tuple[UnverifiedItem, ...] = ()


@dataclass(frozen=True)
class DM14Result:
    candidate_id: str
    drill: RollbackDrillResult
    unverified: tuple[UnverifiedItem, ...]
    verified: bool
    audit: dict[str, str] = field(default_factory=dict)


class RollbackDrill:
    """确定性的回滚演练：有 rollback_commit 时全部步骤通过并可回滚。"""

    def run(self, candidate: ReleaseCandidate) -> RollbackDrillResult:
        if not candidate.rollback_commit:
            return RollbackDrillResult(
                passed=False,
                steps=tuple((step, False) for step in candidate.steps),
                rolled_back=False,
            )
        return RollbackDrillResult(
            passed=True,
            steps=tuple((step, True) for step in candidate.steps),
            rolled_back=True,
        )


class RuntimeEvent:
    def __init__(self, drill: RollbackDrill | None = None) -> None:
        self.drill = drill or RollbackDrill()

    def execute(self, input_: DM14Input) -> DM14Result:
        drill = self.drill.run(input_.candidate)
        return DM14Result(
            candidate_id=input_.candidate.candidate_id,
            drill=drill,
            unverified=input_.unverified,
            verified=drill.passed and not input_.unverified,
            audit={
                "version": input_.candidate.version,
                "target_commit": input_.candidate.target_commit,
                "rollback_commit": input_.candidate.rollback_commit,
            },
        )
