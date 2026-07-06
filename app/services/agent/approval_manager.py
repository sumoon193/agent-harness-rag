"""
Approval Manager。

管理审批流程，包括创建、审批、拒绝和编辑审批请求。
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.approval import ApprovalRequest
from app.schemas.enums import ApprovalDecisionType, ApprovalStatus, ToolRiskLevel
from app.schemas.tool import ToolCall
from app.schemas.user import UserContext
from app.services.agent.step_logger import StepLogger

logger = logging.getLogger(__name__)


class ApprovalManager:
    """
    审批管理器。

    管理审批请求的生命周期。
    """

    def __init__(self, step_logger: StepLogger) -> None:
        """
        初始化审批管理器。

        Args:
            step_logger: 步骤记录器
        """
        self._step_logger = step_logger
        self._requests: dict[str, ApprovalRequest] = {}  # approval_id -> request

    def create_request(
        self,
        run_id: str,
        tool_call: ToolCall,
        tool_name: str,
        parameters: dict[str, Any],
        risk_level: ToolRiskLevel,
        user_context: UserContext
    ) -> ApprovalRequest:
        """
        创建审批请求。

        Args:
            run_id: Run ID
            tool_call: 工具调用记录
            tool_name: 工具名称
            parameters: 工具参数
            risk_level: 风险等级
            user_context: 用户上下文

        Returns:
            审批请求
        """
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"

        # 生成预期影响描述
        expected_effect = self._generate_expected_effect(tool_name, parameters)

        # 生成证据（模拟）
        evidence = self._generate_evidence(tool_name, parameters)

        request = ApprovalRequest(
            id=approval_id,
            run_id=run_id,
            tool_call_id=tool_call.id,
            tool_name=tool_name,
            parameters=parameters,
            expected_effect=expected_effect,
            evidence=evidence,
            risk_level=risk_level,
            options=[ApprovalDecisionType.APPROVE, ApprovalDecisionType.EDIT, ApprovalDecisionType.REJECT],
            status=ApprovalStatus.PENDING,
            decision=None,
            decided_by=None,
            decided_at=None
        )

        self._requests[approval_id] = request

        logger.info(
            "approval_request_created",
            extra={
                "approval_id": approval_id,
                "run_id": run_id,
                "tool_name": tool_name,
                "risk_level": risk_level.value
            }
        )

        return request

    def approve(self, approval_id: str, decided_by: str) -> ApprovalRequest:
        """
        审批通过。

        Args:
            approval_id: 审批请求 ID
            decided_by: 审批人

        Returns:
            更新后的审批请求
        """
        request = self._get_request(approval_id)
        self._validate_pending(request)

        request.status = ApprovalStatus.APPROVED
        request.decision = ApprovalDecisionType.APPROVE
        request.decided_by = decided_by
        request.decided_at = datetime.now(timezone.utc)

        # 记录审计步骤
        self._step_logger.log_step(
            run_id=request.run_id,
            node_name="approval_approved",
            input_data={"approval_id": approval_id},
            output_data={
                "decision": "approve",
                "decided_by": decided_by,
                "tool_name": request.tool_name
            }
        )

        logger.info(
            "approval_granted",
            extra={"approval_id": approval_id, "decided_by": decided_by}
        )

        return request

    def reject(self, approval_id: str, decided_by: str) -> ApprovalRequest:
        """
        拒绝审批。

        Args:
            approval_id: 审批请求 ID
            decided_by: 审批人

        Returns:
            更新后的审批请求
        """
        request = self._get_request(approval_id)
        self._validate_pending(request)

        request.status = ApprovalStatus.REJECTED
        request.decision = ApprovalDecisionType.REJECT
        request.decided_by = decided_by
        request.decided_at = datetime.now(timezone.utc)

        # 记录审计步骤
        self._step_logger.log_step(
            run_id=request.run_id,
            node_name="approval_rejected",
            input_data={"approval_id": approval_id},
            output_data={
                "decision": "reject",
                "decided_by": decided_by,
                "tool_name": request.tool_name
            }
        )

        logger.info(
            "approval_rejected",
            extra={"approval_id": approval_id, "decided_by": decided_by}
        )

        return request

    def edit_and_approve(
        self,
        approval_id: str,
        edited_parameters: dict[str, Any],
        decided_by: str
    ) -> ApprovalRequest:
        """
        编辑参数后审批。

        Args:
            approval_id: 审批请求 ID
            edited_parameters: 编辑后的参数
            decided_by: 审批人

        Returns:
            更新后的审批请求
        """
        request = self._get_request(approval_id)
        self._validate_pending(request)

        # 记录原始参数
        original_parameters = request.parameters.copy()

        # 更新参数和状态
        request.parameters = edited_parameters
        request.status = ApprovalStatus.APPROVED
        request.decision = ApprovalDecisionType.EDIT
        request.decided_by = decided_by
        request.decided_at = datetime.now(timezone.utc)

        # 记录审计步骤
        self._step_logger.log_step(
            run_id=request.run_id,
            node_name="approval_edited",
            input_data={"approval_id": approval_id},
            output_data={
                "decision": "edit",
                "decided_by": decided_by,
                "original_parameters": original_parameters,
                "edited_parameters": edited_parameters,
                "tool_name": request.tool_name
            }
        )

        logger.info(
            "approval_edited_and_granted",
            extra={"approval_id": approval_id, "decided_by": decided_by}
        )

        return request

    def get_request(self, approval_id: str) -> ApprovalRequest:
        """
        获取审批请求。

        Args:
            approval_id: 审批请求 ID

        Returns:
            审批请求
        """
        return self._get_request(approval_id)

    def get_pending_requests(self, run_id: str) -> list[ApprovalRequest]:
        """
        获取指定 Run 的待审批请求。

        Args:
            run_id: Run ID

        Returns:
            待审批请求列表
        """
        return [
            r for r in self._requests.values()
            if r.run_id == run_id and r.status == ApprovalStatus.PENDING
        ]

    def get_all_requests(self, run_id: str) -> list[ApprovalRequest]:
        """
        获取指定 Run 的所有审批请求。

        Args:
            run_id: Run ID

        Returns:
            审批请求列表
        """
        return [r for r in self._requests.values() if r.run_id == run_id]

    def _get_request(self, approval_id: str) -> ApprovalRequest:
        """获取审批请求（内部方法）。"""
        if approval_id not in self._requests:
            raise NotFoundError(f"Approval request not found: {approval_id}")
        return self._requests[approval_id]

    def _validate_pending(self, request: ApprovalRequest) -> None:
        """验证请求是否为待审批状态。"""
        if request.status != ApprovalStatus.PENDING:
            raise ValidationError(
                f"Approval request {request.id} is not pending (current status: {request.status.value})"
            )

    def _generate_expected_effect(self, tool_name: str, parameters: dict[str, Any]) -> str:
        """生成预期影响描述。"""
        if tool_name == "create_mock_hr_ticket":
            title = parameters.get("title", "未命名工单")
            return f"将创建一个 HR 工单：{title}"
        else:
            return f"将执行工具 {tool_name}"

    def _generate_evidence(self, tool_name: str, parameters: dict[str, Any]) -> list[dict]:
        """生成证据（模拟）。"""
        return [
            {
                "source": "user_request",
                "content": f"用户请求执行 {tool_name}",
                "confidence": 0.9
            }
        ]
