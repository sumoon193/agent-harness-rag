"""
Agent Safety Eval Schema。
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SafetyRiskCategory(str, Enum):
    """Agent Harness 安全风险类别。"""

    UNAUTHORIZED_RETRIEVAL = "unauthorized_retrieval"
    PROMPT_INJECTION = "prompt_injection"
    MISSING_CITATION = "missing_citation"
    WRITE_TOOL_MISUSE = "write_tool_misuse"
    COST_OVERRUN = "cost_overrun"


class SafetyEvalCase(BaseModel):
    """单条安全评测用例。"""

    id: str = Field(description="用例 ID")
    category: SafetyRiskCategory = Field(description="风险类别")
    input_text: str = Field(description="输入文本或问题")
    expected_behavior: str = Field(description="期望行为")
    forbidden_behavior: str = Field(description="禁止行为")
    observations: dict[str, Any] = Field(
        default_factory=dict,
        description="待评测的结构化观测结果",
    )
    run_id: str | None = Field(default=None, description="关联 AgentRun ID")
    trace_id: str | None = Field(default=None, description="关联 trace ID")
    artifact_path: str | None = Field(default=None, description="关联 artifact 路径")


class SafetyEvalResult(BaseModel):
    """单条安全评测结果。"""

    case_id: str = Field(description="用例 ID")
    category: SafetyRiskCategory = Field(description="风险类别")
    passed: bool = Field(description="是否通过")
    failure_reason: str | None = Field(default=None, description="失败原因")
    run_id: str | None = Field(default=None, description="关联 AgentRun ID")
    trace_id: str | None = Field(default=None, description="关联 trace ID")
    artifact_path: str | None = Field(default=None, description="关联 artifact 路径")


class SafetyEvalReport(BaseModel):
    """安全评测报告。"""

    total_cases: int = Field(description="总用例数")
    passed_cases: int = Field(description="通过用例数")
    failed_case_ids: list[str] = Field(default_factory=list, description="失败用例 ID")
    pass_rate: float = Field(description="总体通过率")
    pass_rate_by_category: dict[str, float] = Field(
        default_factory=dict,
        description="各风险类别通过率",
    )
    results: list[SafetyEvalResult] = Field(
        default_factory=list,
        description="单条结果",
    )
