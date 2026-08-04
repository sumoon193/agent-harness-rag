"""devmate 模型 diagnosis 领域类型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TypedDiagnosis:
    diagnosis_id: str
    summary: str
    severity: str
    rule: str
    confidence: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class DM07Input:
    case_id: str
    mode: str = "fake"
    raw_output: str = ""
    recorded: dict[str, str] | None = None


@dataclass(frozen=True)
class DM07Result:
    case_id: str
    diagnosis: TypedDiagnosis
    mode: str
    degraded: bool
    audit: dict[str, str]
