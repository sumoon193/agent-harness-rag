"""devmate 确定性诊断领域模型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiagnosticFinding:
    finding_id: str
    severity: str
    rule: str
    message: str
    source: str
    line: int


@dataclass(frozen=True)
class DM06Input:
    log_text: str
    report_text: str
    source: str = "diagnostics"
    baseline_id: str = "bl-1"


@dataclass(frozen=True)
class DM06Result:
    baseline_id: str
    findings: tuple[DiagnosticFinding, ...]
    finding_count: int
    signature: str
