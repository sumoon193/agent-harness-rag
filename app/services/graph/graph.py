"""
LangGraph StateGraph 定义。

定义 Agent Graph 的结构和编译。
"""
from __future__ import annotations

import logging

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.services.agent.run_manager import AgentRunManager
from app.services.graph.edges import (
    after_approval_route,
    after_evidence_route,
    after_intent_route,
    after_plan_route,
)
from app.services.graph.nodes import (
    answer_node,
    approval_gate_node,
    evidence_score_node,
    fact_check_node,
    finalize_node,
    intent_node,
    plan_node,
    query_rewrite_node,
    retrieve_node,
    tool_execute_node,
)
from app.services.graph.state import AgentGraphState
from app.services.retrieval.hybrid import HybridRetriever

logger = logging.getLogger(__name__)


def create_agent_graph(
    run_manager: AgentRunManager,
    hybrid_retriever: HybridRetriever,
    answer_service: object | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> StateGraph:
    """
    创建 Agent Graph。

    Args:
        run_manager: Agent Run Manager
        hybrid_retriever: 混合检索器
        answer_service: 答案生成服务（可选）
        checkpointer: 编译 graph 用的 checkpointer；未注入时回退进程内
            MemorySaver（测试/fallback 场景），生产持久化后端由
            app.services.graph.checkpointer 工厂按 settings 构建并注入

    Returns:
        编译后的 StateGraph
    """
    logger.info("creating_agent_graph")

    # 创建 graph
    graph = StateGraph(AgentGraphState)

    # 添加节点（使用 partial 绑定依赖）
    from functools import partial

    graph.add_node("intent", partial(intent_node, run_manager=run_manager))
    graph.add_node("query_rewrite", partial(query_rewrite_node, run_manager=run_manager))
    graph.add_node("retrieve", partial(retrieve_node, run_manager=run_manager, hybrid_retriever=hybrid_retriever))
    graph.add_node("evidence_score", partial(evidence_score_node, run_manager=run_manager))
    graph.add_node("plan", partial(plan_node, run_manager=run_manager))
    graph.add_node("approval_gate", partial(approval_gate_node, run_manager=run_manager))
    graph.add_node("tool_execute", partial(tool_execute_node, run_manager=run_manager))
    graph.add_node("answer", partial(answer_node, run_manager=run_manager, answer_service=answer_service))
    graph.add_node("fact_check", partial(fact_check_node, run_manager=run_manager))
    graph.add_node("finalize", partial(finalize_node, run_manager=run_manager))

    # 添加边
    graph.add_edge(START, "intent")
    graph.add_conditional_edges("intent", after_intent_route)
    graph.add_edge("query_rewrite", "retrieve")
    graph.add_edge("retrieve", "evidence_score")
    graph.add_conditional_edges("evidence_score", after_evidence_route)
    graph.add_conditional_edges("plan", after_plan_route)
    graph.add_conditional_edges("approval_gate", after_approval_route)
    graph.add_edge("tool_execute", "answer")
    graph.add_edge("answer", "fact_check")
    graph.add_edge("fact_check", "finalize")
    graph.add_edge("finalize", END)

    # checkpointer 由调用方（ServiceContainer）根据 settings 注入：
    # postgres 后端使用 AsyncPostgresSaver 持久化 checkpoint，进程重启后
    # waiting_approval 的长流程仍可 resume；未注入时回退进程内 MemorySaver。
    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver

        checkpointer = MemorySaver()

    compiled = graph.compile(checkpointer=checkpointer)

    logger.info("agent_graph_created")
    return compiled
