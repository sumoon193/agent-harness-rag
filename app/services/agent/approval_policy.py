"""
审批策略。

决定哪些审批请求可由策略引擎自动决策，而非等待人工审批。
所有策略实现 ApprovalPolicy Protocol，通过依赖注入接入 Run Manager。
"""
from __future__ import annotations

import logging
from typing import Any, Protocol

from app.schemas.enums import ApprovalDecisionType, ToolRiskLevel
from app.schemas.user import UserContext

logger = logging.getLogger(__name__)

# 自动审批使用的虚拟审批人身份，用于审计区分策略引擎与真实人工审批。
POLICY_ENGINE_APPROVER = "policy_engine"


class ApprovalPolicy(Protocol):
    """
    审批策略协议。

    外部策略实现此协议；返回 None 表示该请求需要转人工审批。
    """

    def evaluate(
        self,
        *,
        tool_name: str,
        parameters: dict[str, Any],
        risk_level: ToolRiskLevel,
        user_context: UserContext,
    ) -> ApprovalDecisionType | None:
        """返回自动决策；None 表示转人工审批。"""
        ...


class RuleBasedApprovalPolicy:
    """
    基于风险等级的规则策略。

    - WRITE：allow_writes=True 时自动 APPROVE
    - ADMIN：allow_admin=True 时自动 APPROVE（沙箱用，默认 False）
    - READ：不产生审批请求，策略返回 None

    保守默认：写入型自动、管理级人工。
    """

    def __init__(
        self,
        *,
        allow_writes: bool = True,
        allow_admin: bool = False,
    ) -> None:
        self._allow_writes = allow_writes
        self._allow_admin = allow_admin

    def evaluate(
        self,
        *,
        tool_name: str,
        parameters: dict[str, Any],
        risk_level: ToolRiskLevel,
        user_context: UserContext,
    ) -> ApprovalDecisionType | None:
        if risk_level == ToolRiskLevel.WRITE:
            return ApprovalDecisionType.APPROVE if self._allow_writes else None
        if risk_level == ToolRiskLevel.ADMIN:
            return ApprovalDecisionType.APPROVE if self._allow_admin else None
        return None


class NoopApprovalPolicy:
    """从不自动审批（manual 模式），等价于原有人工流程。"""

    def evaluate(
        self,
        *,
        tool_name: str,
        parameters: dict[str, Any],
        risk_level: ToolRiskLevel,
        user_context: UserContext,
    ) -> ApprovalDecisionType | None:
        return None


def build_approval_policy(
    approval_mode: str,
    *,
    allow_admin: bool = False,
) -> ApprovalPolicy:
    """
    按 APPROVAL_MODE 构建审批策略。

    - manual：全部转人工（默认，等价原流程）
    - policy：写入型工具自动批准，管理级转人工
    - auto：写入型自动；allow_admin=True 时管理级也自动（沙箱）
    """
    if approval_mode == "auto":
        return RuleBasedApprovalPolicy(allow_writes=True, allow_admin=allow_admin)
    if approval_mode == "policy":
        return RuleBasedApprovalPolicy(allow_writes=True, allow_admin=False)
    return NoopApprovalPolicy()
