"""
审批相关 Schema。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import ApprovalDecisionType, ApprovalStatus, ToolRiskLevel


class ApprovalRequest(BaseModel):
    """
    审批请求。

    当写入型工具触发时创建，等待人工审批。
    """
    id: str = Field(description="审批请求 ID，前缀 appr_")
    run_id: str = Field(description="所属 Run ID")
    tool_call_id: str = Field(description="工具调用 ID")
    tool_name: str = Field(description="工具名称")
    parameters: dict[str, Any] = Field(description="工具参数")
    expected_effect: str = Field(description="预期影响描述")
    evidence: list[dict] = Field(
        default_factory=list,
        description="相关证据（前 3 条）"
    )
    risk_level: ToolRiskLevel = Field(description="风险等级")
    options: list[ApprovalDecisionType] = Field(
        default_factory=lambda: [
            ApprovalDecisionType.APPROVE,
            ApprovalDecisionType.EDIT,
            ApprovalDecisionType.REJECT,
        ],
        description="审批选项"
    )
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING,
        description="审批状态（pending/approved/rejected/edited）"
    )
    decision: ApprovalDecisionType | None = Field(
        default=None,
        description="审批决策（approve/edit/reject）"
    )
    decided_by: str | None = Field(
        default=None,
        description="审批人用户 ID"
    )
    decided_at: datetime | None = Field(
        default=None,
        description="审批时间（UTC）"
    )
    revision: int = Field(default=1, ge=1, description="审批修订号")
    subject_hash: str = Field(default="", description="审批对象内容哈希")
    requested_by: str | None = Field(default=None, description="审批发起人")
    requested_at: datetime | None = Field(default=None, description="审批发起时间")
    expires_at: datetime | None = Field(default=None, description="审批失效时间")
    policy_version: str = Field(default="", description="绑定的策略版本")
    execution_manifest_hash: str = Field(default="", description="绑定的执行清单哈希")
    supersedes_approval_id: str | None = Field(default=None, description="被替代审批 ID")
    revoked_by: str | None = Field(default=None, description="撤销人")
    revoked_at: datetime | None = Field(default=None, description="撤销时间")
    revoke_reason: str | None = Field(default=None, description="撤销原因")

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    """
    审批决策提交。

    用户提交审批结果时使用。
    """
    decision: ApprovalDecisionType = Field(
        description="审批决策（approve/edit/reject）"
    )
    edited_parameters: dict[str, Any] | None = Field(
        default=None,
        description="编辑后的参数（仅 decision=edit 时使用）"
    )
