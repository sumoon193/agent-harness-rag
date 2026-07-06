"""
Agent Run 相关 Schema。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import RunStatus
from app.schemas.tool import ToolCall


class AgentRunCreate(BaseModel):
    """创建 Agent Run 的请求体。"""
    query: str = Field(description="用户查询")
    user_id: str = Field(description="用户 ID")


class AgentStep(BaseModel):
    """
    Agent 执行步骤。

    记录单个节点的输入输出、证据和 token 消耗。
    """
    id: str = Field(description="步骤 ID")
    run_id: str = Field(description="所属 Run ID")
    node_name: str = Field(description="节点名称（如 intent, retrieve, generate）")
    input_data: dict[str, Any] = Field(
        default_factory=dict,
        description="输入数据"
    )
    output_data: dict[str, Any] = Field(
        default_factory=dict,
        description="输出数据"
    )
    evidence: list[dict] = Field(
        default_factory=list,
        description="相关证据（如有）"
    )
    token_usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token 使用情况（prompt_tokens, completion_tokens）"
    )
    duration_ms: int = Field(
        default=0,
        description="执行耗时（毫秒）"
    )
    created_at: datetime = Field(description="创建时间（UTC）")

    model_config = {"from_attributes": True}


class AgentPlan(BaseModel):
    """
    Agent 执行计划。

    包含计划步骤和当前执行位置。
    """
    id: str = Field(description="计划 ID")
    run_id: str = Field(description="所属 Run ID")
    steps: list[str] = Field(description="计划步骤列表（工具名称）")
    current_step_index: int = Field(
        default=0,
        description="当前执行步骤索引"
    )

    model_config = {"from_attributes": True}


class AgentRunResponse(BaseModel):
    """
    Agent Run 响应体。

    包含 Run 完整信息：状态、步骤、工具调用和结果。
    """
    id: str = Field(description="Run ID，前缀 run_")
    user_id: str = Field(description="用户 ID")
    thread_id: str = Field(description="LangGraph thread ID")
    original_query: str = Field(description="原始查询")
    status: RunStatus = Field(description="当前状态")
    steps: list[AgentStep] = Field(
        default_factory=list,
        description="执行步骤列表"
    )
    tool_calls: list[ToolCall] = Field(
        default_factory=list,
        description="工具调用记录"
    )
    result: dict | None = Field(
        default=None,
        description="最终结果（答案、citations 等）"
    )
    created_at: datetime = Field(description="创建时间（UTC）")
    completed_at: datetime | None = Field(
        default=None,
        description="完成时间（UTC）"
    )

    model_config = {"from_attributes": True}
