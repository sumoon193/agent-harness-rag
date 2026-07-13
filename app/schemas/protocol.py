"""MCP 与 A2A 协议边界 Schema。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JsonRpcRequest(BaseModel):
    """MCP Streamable HTTP 使用的 JSON-RPC 请求。"""

    jsonrpc: str = "2.0"
    id: str | int
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class JsonRpcResponse(BaseModel):
    """JSON-RPC 成功或错误响应。"""

    jsonrpc: str = "2.0"
    id: str | int
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class AgentCard(BaseModel):
    """A2A peer 的能力与安全边界声明。"""

    name: str
    description: str
    version: str
    url: str
    capabilities: dict[str, Any] = Field(default_factory=dict)
    skills: list[dict[str, Any]] = Field(default_factory=list)


class A2AMessage(BaseModel):
    """A2A Task 内的消息。"""

    id: str
    role: str
    text: str
    created_at: datetime


class ArtifactRef(BaseModel):
    """协议任务返回的可追溯 artifact。"""

    id: str
    name: str
    mime_type: str
    uri: str
    content: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProtocolTask(BaseModel):
    """A2A goal-oriented 长任务的本地表示。"""

    id: str
    context_id: str
    status: str
    messages: list[A2AMessage] = Field(default_factory=list)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
