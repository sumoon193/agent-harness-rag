"""RepairPlan：从 findings 生成不可变 patch artifact。

artifact 以 frozen dataclass 构造，digest 在构造时固化，之后任何修改
都会抛出 AttributeError；同一输入产生同一 digest 与签名。
"""

from __future__ import annotations

import hashlib

from app.devmate.repair.types import DM08Input, DM08Result, PatchArtifact, RepairStep


class EmptyPlanError(ValueError):
    """没有 findings 时不能生成修复计划。"""


class RepairPlan:
    def create(self, input_: DM08Input) -> DM08Result:
        if not input_.findings:
            raise EmptyPlanError("no findings to repair")
        steps: list[RepairStep] = []
        artifacts: list[PatchArtifact] = []
        for index, (rule, message) in enumerate(input_.findings, start=1):
            artifact = _build_artifact(rule, message, input_.target_root, input_.base_sha)
            artifacts.append(artifact)
            steps.append(RepairStep(step_id=f"step-{index}", rule=rule, artifact=artifact))
        signature = _signature(tuple(artifact.digest for artifact in artifacts))
        return DM08Result(
            case_id=input_.case_id,
            plan_id=_plan_id(input_.case_id, signature),
            steps=tuple(steps),
            artifacts=tuple(artifacts),
            immutable_signature=signature,
        )


def _build_artifact(rule: str, message: str, target_root: str, base_sha: str) -> PatchArtifact:
    content = (
        f"--- a/{rule}.py\n"
        f"+++ b/{rule}.py\n"
        f"@@ -1 +1 @@\n"
        f"-{message}\n"
        f"+fixed: {message}\n"
        f"base: {base_sha}\n"
    )
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return PatchArtifact(
        patch_id=f"patch-{rule}-{digest[:8]}",
        path=f"{target_root}/{rule}.patch",
        kind="edit",
        content=content,
        digest=digest,
    )


def _signature(digests: tuple[str, ...]) -> str:
    canonical = "\n".join(digests)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _plan_id(case_id: str, signature: str) -> str:
    return f"plan-{case_id}-{signature[:8]}"
