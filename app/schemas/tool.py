"""
工具定义与调用 Schema。
"""
from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import ToolCallStatus, ToolRiskLevel


class ToolDefinition(BaseModel):
    """
    工具定义。

    包含工具元数据、风险等级和参数 schema。
    """
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    permission_scope: str = Field(
        description="权限范围（如 hr.document.read）"
    )
    risk_level: ToolRiskLevel = Field(description="风险等级")
    requires_approval: bool = Field(
        description="是否需要人工审批"
    )
    timeout_seconds: int = Field(
        default=30,
        description="超时时间（秒）"
    )
    idempotent: bool = Field(
        default=False,
        description="是否幂等"
    )
    parameters_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="参数 JSON Schema"
    )

    @model_validator(mode="after")
    def validate_approval_policy(self) -> Self:
        """写入型和管理型工具必须开启人工审批。"""
        requires_manual_review = self.risk_level in {
            ToolRiskLevel.WRITE,
            ToolRiskLevel.ADMIN,
        }
        if requires_manual_review and not self.requires_approval:
            raise ValueError("write and admin tools must require approval")
        return self

    model_config = {"from_attributes": True}


class ToolCall(BaseModel):
    """
    工具调用记录。

    记录单次工具调用的参数、结果和状态。
    """
    id: str = Field(description="工具调用 ID，前缀 tool_")
    run_id: str = Field(description="所属 Run ID")
    tool_name: str = Field(description="工具名称")
    parameters: dict[str, Any] = Field(
        description="调用参数"
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="执行结果"
    )
    status: ToolCallStatus = Field(
        default=ToolCallStatus.PENDING,
        description="调用状态（pending/approved/rejected/completed/failed）"
    )
    approval_required: bool = Field(
        description="是否需要审批"
    )

    model_config = {"from_attributes": True}
