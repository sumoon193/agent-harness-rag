"""
Agent 自定义指标。

计算 Agent 层面的评测指标：工具调用准确率、审批正确率等。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AgentMetricsResult:
    """
    Agent 指标计算结果。
    """
    tool_call_accuracy: float = 0.0
    approval_correctness: float = 0.0
    agent_goal_completion_rate: float = 0.0
    refusal_correctness: float = 0.0
    total_cases: int = 0
    details: list[dict[str, object]] = field(default_factory=list)


def compute_agent_metrics(
    eval_cases: list[dict[str, object]],
) -> AgentMetricsResult:
    """
    计算 Agent 自定义指标。

    每条 eval_case 需包含：
    - expected_tools: list[str]  预期工具
    - actual_tools: list[str]    实际调用的工具
    - requires_approval: bool    是否需要审批
    - approval_granted: bool     是否正确处理了审批（True=批准/拒绝均算正确）
    - expected_refusal: bool     是否预期拒答
    - actual_refused: bool       是否实际拒答
    - goal_completed: bool       是否完成目标

    Args:
        eval_cases: 评测用例列表

    Returns:
        AgentMetricsResult
    """
    if not eval_cases:
        return AgentMetricsResult()

    correct_tool_calls = 0
    correct_approvals = 0
    approval_cases = 0
    correct_refusals = 0
    refusal_cases = 0
    goals_completed = 0
    details: list[dict[str, object]] = []

    for case in eval_cases:
        expected_tools = set(case.get("expected_tools", []))  # type: ignore[arg-type]
        actual_tools = set(case.get("actual_tools", []))  # type: ignore[arg-type]

        # 工具调用准确率：预期工具集 == 实际工具集
        tool_correct = expected_tools == actual_tools
        if tool_correct:
            correct_tool_calls += 1

        # 审批正确率
        requires_approval = case.get("requires_approval", False)  # type: ignore[assignment]
        if requires_approval:
            approval_cases += 1
            approval_granted = case.get("approval_granted", False)  # type: ignore[assignment]
            if approval_granted:
                correct_approvals += 1

        # 拒答正确率
        expected_refusal = case.get("expected_refusal", False)  # type: ignore[assignment]
        if expected_refusal:
            refusal_cases += 1
            actual_refused = case.get("actual_refused", False)  # type: ignore[assignment]
            if actual_refused:
                correct_refusals += 1

        # 目标完成率
        if case.get("goal_completed", False):  # type: ignore[assignment]
            goals_completed += 1

        details.append({
            "case_id": case.get("case_id", ""),
            "tool_correct": tool_correct,
        })

    total = len(eval_cases)
    result = AgentMetricsResult(
        tool_call_accuracy=round(correct_tool_calls / total, 3) if total else 0.0,
        approval_correctness=round(correct_approvals / approval_cases, 3) if approval_cases else 1.0,
        agent_goal_completion_rate=round(goals_completed / total, 3) if total else 0.0,
        refusal_correctness=round(correct_refusals / refusal_cases, 3) if refusal_cases else 1.0,
        total_cases=total,
        details=details,
    )

    logger.info(
        "agent_metrics_computed",
        extra={
            "tool_call_accuracy": result.tool_call_accuracy,
            "approval_correctness": result.approval_correctness,
            "goal_completion_rate": result.agent_goal_completion_rate,
            "refusal_correctness": result.refusal_correctness,
            "total": total,
        },
    )
    return result
