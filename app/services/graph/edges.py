"""
LangGraph 路由条件。

定义 Graph 中各个节点的路由逻辑。
"""
from __future__ import annotations

import logging

from app.services.graph.state import AgentGraphState

logger = logging.getLogger(__name__)


def after_intent_route(state: AgentGraphState) -> str:
    """
    意图分析后的路由。

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    intent = state.get("intent", "hr_query")

    logger.info("routing_after_intent", extra={"intent": intent})

    if intent == "tool_request":
        return "plan"
    elif intent == "clarification":
        return "answer"
    else:
        return "query_rewrite"


def after_evidence_route(state: AgentGraphState) -> str:
    """
    证据检索后的路由。

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    evidence = state.get("evidence")

    logger.info("routing_after_evidence", extra={"has_evidence": evidence is not None})

    if evidence and evidence.get("total_count", 0) > 0:
        return "plan"
    else:
        return "answer"


def after_plan_route(state: AgentGraphState) -> str:
    """
    计划生成后的路由。

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    plan = state.get("plan")
    intent = state.get("intent", "hr_query")

    logger.info("routing_after_plan", extra={"has_plan": plan is not None, "intent": intent})

    if intent == "tool_request" and plan and plan.steps:
        return "approval_gate"
    else:
        return "answer"


def after_approval_route(state: AgentGraphState) -> str:
    """
    审批门控后的路由。

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    pending_tool_call = state.get("pending_tool_call")
    approval_decision = state.get("approval_decision")

    logger.info(
        "routing_after_approval",
        extra={
            "has_pending": pending_tool_call is not None,
            "has_decision": approval_decision is not None
        }
    )

    if pending_tool_call and approval_decision:
        # 有审批决策，执行工具
        return "tool_execute"
    elif pending_tool_call and not approval_decision:
        # 需要审批但没有决策（interrupt 后）
        return "finalize"
    else:
        # 不需要审批
        return "answer"
