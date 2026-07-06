"""
Loop Engineering 服务。

把 plan、act、observe、reflect、repair 固化为 Harness 可审计事件。
"""
from __future__ import annotations

import uuid

from app.core.exceptions import ValidationError
from app.schemas.harness import LoopDecision, LoopEvent, LoopStage
from app.services.agent.step_logger import StepLogger


class LoopEngine:
    """Agent Loop 治理事件记录器。"""

    def __init__(self, step_logger: StepLogger) -> None:
        self._step_logger = step_logger

    def record_plan(
        self,
        run_id: str,
        plan_id: str,
        steps: list[str],
    ) -> LoopEvent:
        """记录 PLAN 事件。"""
        event = self._create_event(
            run_id=run_id,
            stage=LoopStage.PLAN,
            decision=LoopDecision.CONTINUE,
            reasons=[],
            action="execute_plan",
            metadata={"plan_id": plan_id, "steps": steps},
        )
        self._log_event(event, "plan_event_created")
        return event

    def observe(
        self,
        run_id: str,
        observation: dict[str, object],
    ) -> LoopEvent:
        """记录 OBSERVE 事件。"""
        event = self._create_event(
            run_id=run_id,
            stage=LoopStage.OBSERVE,
            decision=LoopDecision.CONTINUE,
            reasons=[],
            action="record_observation",
            metadata=observation,
        )
        self._log_event(event, "observation_created")
        return event

    def reflect(
        self,
        run_id: str,
        evidence_count: int,
        has_citations: bool,
        tool_error: str | None,
        approval_pending: bool,
    ) -> LoopEvent:
        """
        根据当前观测结果生成 reflection。

        Reflection 只能给出治理建议，不能绕过审批执行写操作。
        """
        reasons: list[str] = []
        metadata: dict[str, object] = {
            "evidence_count": evidence_count,
            "has_citations": has_citations,
            "approval_pending": approval_pending,
        }
        if tool_error:
            metadata["tool_error"] = tool_error

        if approval_pending:
            reasons.append("approval_pending")
            event = self._create_event(
                run_id=run_id,
                stage=LoopStage.REFLECT,
                decision=LoopDecision.AWAIT_APPROVAL,
                reasons=reasons,
                action="wait_for_human_approval",
                metadata=metadata,
            )
            self._log_event(event, "reflection_created")
            return event

        if evidence_count <= 0:
            reasons.append("insufficient_evidence")
        if not has_citations:
            reasons.append("missing_citations")
        if tool_error:
            reasons.append("tool_failed")

        decision = LoopDecision.REPAIR if reasons else LoopDecision.CONTINUE
        action = "create_repair_action" if reasons else "continue"
        event = self._create_event(
            run_id=run_id,
            stage=LoopStage.REFLECT,
            decision=decision,
            reasons=reasons,
            action=action,
            metadata=metadata,
        )
        self._log_event(event, "reflection_created")
        return event

    def create_repair_action(
        self,
        run_id: str,
        reflection: LoopEvent,
    ) -> LoopEvent:
        """根据 reflection 生成 repair 动作。"""
        if reflection.decision != LoopDecision.REPAIR:
            raise ValidationError("Only repair reflections can create repair actions")

        action = self._choose_repair_action(reflection)
        previous_failure_reason = self._build_previous_failure_reason(reflection)
        event = self._create_event(
            run_id=run_id,
            stage=LoopStage.REPAIR,
            decision=LoopDecision.CONTINUE,
            reasons=reflection.reasons,
            action=action,
            previous_failure_reason=previous_failure_reason,
            metadata={
                "reflection_id": reflection.id,
                "previous_failure_reason": previous_failure_reason,
            },
        )
        self._log_event(event, "repair_action_created")
        return event

    def _create_event(
        self,
        run_id: str,
        stage: LoopStage,
        decision: LoopDecision,
        reasons: list[str],
        action: str | None,
        metadata: dict[str, object],
        previous_failure_reason: str | None = None,
    ) -> LoopEvent:
        """创建 LoopEvent。"""
        return LoopEvent(
            id=f"loop_{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            stage=stage,
            decision=decision,
            reasons=reasons,
            action=action,
            previous_failure_reason=previous_failure_reason,
            metadata=metadata,
        )

    def _log_event(self, event: LoopEvent, node_name: str) -> None:
        """将 LoopEvent 写入 StepLogger。"""
        self._step_logger.log_step(
            run_id=event.run_id,
            node_name=node_name,
            input_data={"stage": event.stage.value},
            output_data=event.model_dump(mode="json"),
        )

    def _choose_repair_action(self, reflection: LoopEvent) -> str:
        """根据失败原因选择修复动作。"""
        if "tool_failed" in reflection.reasons:
            return "retry_tool_or_fallback"
        if "missing_citations" in reflection.reasons and "insufficient_evidence" not in reflection.reasons:
            return "rebuild_citations_or_refuse"
        return "retry_retrieval"

    def _build_previous_failure_reason(self, reflection: LoopEvent) -> str:
        """构建可复盘的失败原因。"""
        if "tool_failed" in reflection.reasons:
            tool_error = reflection.metadata.get("tool_error", "")
            return f"tool_failed:{tool_error}"
        return ";".join(reflection.reasons)
