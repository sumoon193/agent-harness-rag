"""
GraphState 定义。

定义 LangGraph StateGraph 的状态结构。
"""
from __future__ import annotations

from typing import TypedDict

from app.schemas.agent import AgentPlan
from app.schemas.approval import ApprovalDecision
from app.schemas.chunk import EvidenceBundle
from app.schemas.tool import ToolCall
from app.schemas.user import UserContext


class AgentGraphState(TypedDict):
    """
    Agent Graph 状态。

    包含 Agent 执行过程中所有需要的状态信息。
    """

    # 基本信息
    run_id: str
    thread_id: str
    user: UserContext
    question: str

    # 意图分析
    intent: str | None  # hr_query, tool_request, clarification
    rewritten_queries: list[str]

    # 证据
    evidence: EvidenceBundle | None

    # 计划
    plan: AgentPlan | None

    # 工具执行
    pending_tool_call: ToolCall | None
    pending_approval_id: str | None
    approval_decision: ApprovalDecision | None
    tool_results: list[ToolCall]

    # 答案
    answer: dict | None

    # 错误
    errors: list[str]
