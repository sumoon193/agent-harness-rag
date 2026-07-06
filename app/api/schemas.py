"""
API 层 Schema。

只在 API 边界使用，不暴露 ORM 模型或内部领域对象。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import RunStatus


# ── 通用 ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str = Field(default="ok")
    version: str = Field(default="0.1.0")
    timestamp: datetime
    mode: str = Field(default="fallback")
    services: dict[str, dict[str, Any]] = Field(default_factory=dict)


# ── Document ──────────────────────────────────────────────────────────

class DocumentCreateRequest(BaseModel):
    """文档上传请求（不含文件内容，V1 用 metadata 占位）。"""
    title: str = Field(min_length=1, max_length=500, description="文档标题")
    tenant_id: str = Field(description="租户 ID")
    department_id: str = Field(description="部门 ID")
    visibility: str = Field(default="department", description="可见性")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class DocumentCreateResponse(BaseModel):
    """文档上传响应。"""
    id: str = Field(description="文档 ID")
    task_id: str = Field(description="入库任务 ID")
    status: str = Field(description="入库状态")
    message: str = Field(default="文档已接收，正在处理")


class IngestionStatusResponse(BaseModel):
    """异步入库任务状态。"""
    task_id: str = Field(description="任务 ID")
    document_id: str = Field(description="文档 ID")
    status: str = Field(description="任务状态")
    progress: float = Field(ge=0.0, le=1.0, description="进度")
    error_message: str | None = Field(default=None)


# ── Agent Run ─────────────────────────────────────────────────────────

class AgentRunCreateRequest(BaseModel):
    """创建 Agent Run 请求。"""
    query: str = Field(min_length=1, max_length=2000, description="用户查询")
    user_id: str = Field(description="用户 ID")


class AgentRunSummary(BaseModel):
    """Agent Run 概览（列表用）。"""
    id: str
    status: RunStatus
    original_query: str
    created_at: datetime
    completed_at: datetime | None = None


class AgentRunDetail(BaseModel):
    """Agent Run 详情。"""
    id: str
    user_id: str
    thread_id: str
    original_query: str
    status: RunStatus
    steps: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AgentRunCreateResponse(BaseModel):
    """创建 Agent Run 响应。"""
    id: str = Field(description="Run ID")
    thread_id: str = Field(description="Thread ID")
    status: RunStatus
    message: str = Field(default="Agent Run 已创建")


# ── Approval ──────────────────────────────────────────────────────────

class ApprovalSubmitRequest(BaseModel):
    """审批提交请求。"""
    decision: str = Field(description="审批决策：approve / edit / reject")
    edited_parameters: dict[str, Any] | None = Field(
        default=None,
        description="编辑后的参数（仅 decision=edit 时）"
    )


class ApprovalSubmitResponse(BaseModel):
    """审批提交响应。"""
    approval_id: str
    status: str
    decision: str


# ── Eval ──────────────────────────────────────────────────────────────

class EvalRunRequest(BaseModel):
    """触发评测请求。"""
    dataset_path: str | None = Field(
        default=None,
        description="Golden Dataset 路径（空则使用默认）"
    )


class SafetyEvalRunRequest(BaseModel):
    """触发 Agent Safety Eval 请求。"""
    cases: list[dict[str, Any]] | None = Field(
        default=None,
        description="安全评测样例；为空时使用默认 deterministic 样例",
    )


class EvalRunResponse(BaseModel):
    """评测运行响应。"""
    run_id: str
    status: str
    metrics: dict[str, float] = Field(default_factory=dict)
    message: str = Field(default="评测完成")
