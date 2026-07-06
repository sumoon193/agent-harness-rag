"""
Agent Run 状态机。

验证状态流转是否合法。
"""
from __future__ import annotations

import logging

from app.core.exceptions import ValidationError
from app.schemas.enums import RunStatus

logger = logging.getLogger(__name__)


class AgentStateMachine:
    """
    Agent Run 状态机。

    严格按照规范的状态流转规则：
    - created -> running
    - running -> retrieving_evidence
    - retrieving_evidence -> planning
    - planning -> awaiting_approval
    - planning -> completed
    - awaiting_approval -> resumed
    - awaiting_approval -> cancelled
    - resumed -> completed
    - resumed -> failed
    """

    # 允许的状态流转
    TRANSITIONS: dict[RunStatus, list[RunStatus]] = {
        RunStatus.CREATED: [RunStatus.RUNNING],
        RunStatus.RUNNING: [RunStatus.RETRIEVING_EVIDENCE, RunStatus.PLANNING, RunStatus.COMPLETED, RunStatus.FAILED],
        RunStatus.RETRIEVING_EVIDENCE: [RunStatus.PLANNING, RunStatus.COMPLETED, RunStatus.FAILED],
        RunStatus.PLANNING: [RunStatus.AWAITING_APPROVAL, RunStatus.COMPLETED, RunStatus.FAILED],
        RunStatus.AWAITING_APPROVAL: [RunStatus.RESUMED, RunStatus.CANCELLED, RunStatus.FAILED],
        RunStatus.RESUMED: [RunStatus.COMPLETED, RunStatus.FAILED],
    }

    def validate_transition(self, from_status: RunStatus, to_status: RunStatus) -> bool:
        """
        验证状态流转是否合法。

        Args:
            from_status: 当前状态
            to_status: 目标状态

        Returns:
            是否合法

        Raises:
            ValidationError: 如果状态流转不合法
        """
        allowed = self.TRANSITIONS.get(from_status, [])

        if to_status not in allowed:
            raise ValidationError(
                f"Invalid status transition: {from_status.value} -> {to_status.value}. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )

        logger.info(
            "status_transition_validated",
            extra={"from": from_status.value, "to": to_status.value}
        )

        return True

    def get_allowed_transitions(self, current_status: RunStatus) -> list[RunStatus]:
        """
        获取当前状态允许的流转。

        Args:
            current_status: 当前状态

        Returns:
            允许的目标状态列表
        """
        return self.TRANSITIONS.get(current_status, [])

    def is_terminal(self, status: RunStatus) -> bool:
        """
        检查状态是否为终态。

        Args:
            status: 状态

        Returns:
            是否为终态
        """
        return status in {
            RunStatus.COMPLETED,
            RunStatus.FAILED,
            RunStatus.CANCELLED
        }
