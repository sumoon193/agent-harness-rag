"""MCP Streamable HTTP 与 A2A HTTP/JSON 路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import ServiceContainer, get_container
from app.api.schemas import A2ATaskRequest
from app.schemas.protocol import AgentCard, JsonRpcRequest, JsonRpcResponse, ProtocolTask
from app.schemas.runtime import RuntimeMetricsSnapshot
from app.schemas.user import UserContext

router = APIRouter(tags=["protocols"])


def _protocol_user(user_id: str = "user_protocol") -> UserContext:
    """构造本地协议验收所需的最小权限上下文。"""
    return UserContext(
        user_id=user_id,
        tenant_id="tenant_001",
        department_ids=["dept_hr"],
        role="hr",
        permissions=["hr.document.read", "hr.ticket.write", "agent.artifact.read"],
    )


@router.post("/mcp", response_model=JsonRpcResponse)
async def mcp_streamable_http(
    body: JsonRpcRequest,
    run_id: str = Query(...),
    container: ServiceContainer = Depends(get_container),
) -> JsonRpcResponse:
    """本地 MCP 2025-11-25 JSON-RPC 入口。"""
    return await container.mcp_protocol_server.handle(
        body,
        run_id=run_id,
        user_context=_protocol_user(),
    )


@router.get("/.well-known/agent-card.json", response_model=AgentCard)
async def get_policy_research_agent_card(
    container: ServiceContainer = Depends(get_container),
) -> AgentCard:
    """发布只读 Policy Research AgentCard。"""
    return container.policy_research_agent.get_agent_card()


@router.post("/a2a/tasks", response_model=ProtocolTask)
async def create_a2a_task(
    body: A2ATaskRequest,
    container: ServiceContainer = Depends(get_container),
) -> ProtocolTask:
    """通过本地 HTTP/JSON 委托只读制度研究任务。"""
    return await container.policy_research_agent.send_message(
        context_id=body.context_id,
        text=body.text,
        user_context=_protocol_user(body.user_id),
    )


@router.get("/metrics/runtime", response_model=RuntimeMetricsSnapshot)
async def get_runtime_metrics(
    container: ServiceContainer = Depends(get_container),
) -> RuntimeMetricsSnapshot:
    """返回 Case/Event/Outbox/Approval/Protocol 工程指标快照。"""
    return container.runtime_metrics.snapshot()
