"""
Loop Engineering 服务测试。

覆盖 plan/observe/reflect/repair 固化为可审计 Harness 事件。
"""
from __future__ import annotations

from app.schemas.harness import LoopDecision, LoopStage
from app.services.agent.loop_engine import LoopEngine
from app.services.agent.step_logger import StepLogger


def test_reflection_creates_repair_for_insufficient_evidence() -> None:
    """证据不足时应生成 reflection 和 repair 事件，并保留失败原因。"""
    step_logger = StepLogger()
    engine = LoopEngine(step_logger=step_logger)

    reflection = engine.reflect(
        run_id="run_loop_001",
        evidence_count=0,
        has_citations=False,
        tool_error=None,
        approval_pending=False,
    )
    repair = engine.create_repair_action("run_loop_001", reflection)

    assert reflection.stage == LoopStage.REFLECT
    assert reflection.decision == LoopDecision.REPAIR
    assert reflection.reasons == ["insufficient_evidence", "missing_citations"]
    assert repair.stage == LoopStage.REPAIR
    assert repair.action == "retry_retrieval"
    assert repair.previous_failure_reason == "insufficient_evidence;missing_citations"

    node_names = [step.node_name for step in step_logger.get_steps("run_loop_001")]
    assert node_names == ["reflection_created", "repair_action_created"]


def test_reflection_waits_when_write_tool_is_pending_approval() -> None:
    """写工具待审批时 reflection 只能等待审批，不能生成绕过审批的 repair。"""
    step_logger = StepLogger()
    engine = LoopEngine(step_logger=step_logger)

    reflection = engine.reflect(
        run_id="run_loop_002",
        evidence_count=2,
        has_citations=True,
        tool_error=None,
        approval_pending=True,
    )

    assert reflection.decision == LoopDecision.AWAIT_APPROVAL
    assert reflection.action == "wait_for_human_approval"
    assert reflection.reasons == ["approval_pending"]
    steps = step_logger.get_steps("run_loop_002")
    assert len(steps) == 1
    assert steps[0].node_name == "reflection_created"


def test_tool_error_reflection_repairs_with_failure_reason() -> None:
    """工具失败时 repair 应携带前一次失败原因，便于复盘。"""
    step_logger = StepLogger()
    engine = LoopEngine(step_logger=step_logger)

    reflection = engine.reflect(
        run_id="run_loop_003",
        evidence_count=2,
        has_citations=True,
        tool_error="mcp server timeout",
        approval_pending=False,
    )
    repair = engine.create_repair_action("run_loop_003", reflection)

    assert reflection.decision == LoopDecision.REPAIR
    assert reflection.reasons == ["tool_failed"]
    assert repair.action == "retry_tool_or_fallback"
    assert repair.previous_failure_reason == "tool_failed:mcp server timeout"
