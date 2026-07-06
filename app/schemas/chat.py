"""
聊天请求与回答响应 Schema。

模块 08 — Grounded Answer 与评测。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.chunk import Citation
from app.schemas.tool import ToolCall


class ChatRequest(BaseModel):
    """
    聊天请求体。

    用户发送问题时使用。
    """
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="用户问题"
    )
    thread_id: str | None = Field(
        default=None,
        description="LangGraph thread ID，用于续接对话"
    )


class AnswerResponse(BaseModel):
    """
    回答响应体。

    包含 grounded answer、引用来源、置信度和工具结果。
    """
    answer: str = Field(description="生成的回答文本")
    citations: list[Citation] = Field(
        default_factory=list,
        description="引用来源列表"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="回答置信度（0.0-1.0）"
    )
    refusal_reason: str | None = Field(
        default=None,
        description="拒答原因（低置信度时填充）"
    )
    tool_results: list[ToolCall] = Field(
        default_factory=list,
        description="工具执行结果列表"
    )
    trace_id: str = Field(
        default="",
        description="追踪 ID，用于链路追踪"
    )

    model_config = {"from_attributes": True}
