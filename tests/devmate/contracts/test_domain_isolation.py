"""DevMate 全层领域隔离契约测试。

合同来源：``模块契约.json`` DM-02 ``observable_result``:
"Runtime 候选不直接依赖 HR/RAG 领域接口"。

本测试把 DM-02 的隔离约束从 ``app/devmate/contracts`` 扩展到整个
``app/devmate/**`` —— CI/CD 层不得 import HR/RAG 领域层
(``app.services.*``、``app.schemas.*``、``app.api.*``、``app.models.*``)，
只能依赖标准库、第三方库和 ``app.devmate.*`` 自身。这是 DevMate 作为
独立 CI/CD Agent 子系统的依赖边界不变量。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

DEVMATE_ROOT = Path(__file__).resolve().parents[3] / "app" / "devmate"

# 跨层依赖前缀：app/devmate 不得引用这些 HR/RAG 领域层。
FORBIDDEN_IMPORT_PATTERNS = (
    re.compile(r"^\s*from\s+app\.services(?!\s*\.)", re.MULTILINE),
    re.compile(r"^\s*from\s+app\.schemas(?!\s*\.)", re.MULTILINE),
    re.compile(r"^\s*from\s+app\.api(?!\s*\.)", re.MULTILINE),
    re.compile(r"^\s*from\s+app\.models(?!\s*\.)", re.MULTILINE),
    re.compile(r"^\s*import\s+app\.services(?!\s*\.)", re.MULTILINE),
    re.compile(r"^\s*import\s+app\.schemas(?!\s*\.)", re.MULTILINE),
    re.compile(r"^\s*import\s+app\.api(?!\s*\.)", re.MULTILINE),
    re.compile(r"^\s*import\s+app\.models(?!\s*\.)", re.MULTILINE),
)

# HR/RAG 业务标识符：CI/CD 层不得出现这些 HR 域类型/术语。
HR_DOMAIN_TOKENS = (
    re.compile(r"\bHRCase\b"),
    re.compile(r"\bhr_case\b"),
    re.compile(r"\bhr_policy\b"),
    re.compile(r"\bOnboardingCaseWorkflow\b"),
    re.compile(r"\bhr_onboarding\b"),
    re.compile(r"\bprobation\b"),
    re.compile(r"\bregularization\b"),
)


def _py_sources() -> list[Path]:
    return sorted(DEVMATE_ROOT.rglob("*.py"))


def test_devmate_package_has_sources() -> None:
    sources = _py_sources()
    assert sources, "app/devmate must contain Python sources"


@pytest.mark.parametrize("source", _py_sources(), ids=lambda p: str(p.relative_to(DEVMATE_ROOT)))
def test_devmate_does_not_import_hr_rag_layers(source: Path) -> None:
    """app/devmate 不得 import app.services/app.schemas/app.api/app.models。"""
    text = source.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_IMPORT_PATTERNS:
        match = pattern.search(text)
        assert match is None, (
            f"{source.relative_to(DEVMATE_ROOT)} 引入跨层依赖: {match.group(0)!r}"
        )


@pytest.mark.parametrize("source", _py_sources(), ids=lambda p: str(p.relative_to(DEVMATE_ROOT)))
def test_devmate_has_no_hr_domain_tokens(source: Path) -> None:
    """app/devmate 不得出现 HR 域标识符（HRCase/onboarding/probation 等）。"""
    text = source.read_text(encoding="utf-8")
    for pattern in HR_DOMAIN_TOKENS:
        match = pattern.search(text)
        assert match is None, (
            f"{source.relative_to(DEVMATE_ROOT)} 出现 HR 域术语: {match.group(0)!r}"
        )