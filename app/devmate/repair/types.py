"""devmate 修复计划领域类型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatchArtifact:
    patch_id: str
    path: str
    kind: str
    content: str
    digest: str


@dataclass(frozen=True)
class RepairStep:
    step_id: str
    rule: str
    artifact: PatchArtifact


@dataclass(frozen=True)
class DM08Input:
    case_id: str
    findings: tuple[tuple[str, str], ...]
    target_root: str = "repo"
    base_sha: str = ""


@dataclass(frozen=True)
class DM08Result:
    case_id: str
    plan_id: str
    steps: tuple[RepairStep, ...]
    artifacts: tuple[PatchArtifact, ...]
    immutable_signature: str
