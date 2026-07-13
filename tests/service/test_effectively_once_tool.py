"""写工具 effectively-once 执行语义测试。"""
from __future__ import annotations

from typing import Any

import pytest

from app.schemas.enums import ToolRiskLevel
from app.schemas.tool import ToolDefinition
from app.schemas.user import UserContext
from app.services.agent.approval_manager import ApprovalManager
from app.services.agent.step_logger import StepLogger
from app.services.agent.tool_executor import ToolExecutor
from app.services.agent.tool_registry import ToolRegistry
from app.services.runtime.side_effects import InMemorySideEffectLedger


class CountingWriteHandler:
    """记录真实 handler 调用次数的测试写工具。"""

    def __init__(self) -> None:
        self.calls = 0

    async def execute(
        self,
        parameters: dict[str, Any],
        user_context: UserContext,
    ) -> dict[str, Any]:
        self.calls += 1
        return {"ticket_id": "HR-001", "title": parameters["title"]}


@pytest.mark.asyncio
async def test_resume_reuses_successful_side_effect_result() -> None:
    """同一 tool call 重放不得重复调用写工具 handler。"""
    handler = CountingWriteHandler()
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="create_ticket",
            description="创建测试工单",
            permission_scope="hr.ticket.write",
            risk_level=ToolRiskLevel.WRITE,
            requires_approval=True,
            idempotent=True,
        ),
        handler,
    )
    steps = StepLogger()
    approvals = ApprovalManager(steps)
    ledger = InMemorySideEffectLedger()
    executor = ToolExecutor(
        registry=registry,
        approval_manager=approvals,
        step_logger=steps,
        side_effect_ledger=ledger,
    )
    user = UserContext(
        user_id="user_hr",
        tenant_id="tenant_a",
        department_ids=["dept_hr"],
        role="hr",
        permissions=["hr.ticket.write"],
    )

    tool_call = await executor.execute(
        run_id="run_001",
        tool_name="create_ticket",
        parameters={"title": "新员工入职"},
        user_context=user,
    )
    approval = approvals.get_pending_requests("run_001")[0]
    approvals.approve(approval.id, "user_manager")

    first = await executor.execute_after_approval(
        run_id="run_001",
        tool_call_id=tool_call.id,
        approval_id=approval.id,
        user_context=user,
    )
    replayed = await executor.execute_after_approval(
        run_id="run_001",
        tool_call_id=tool_call.id,
        approval_id=approval.id,
        user_context=user,
    )

    assert first.result == replayed.result == {"ticket_id": "HR-001", "title": "新员工入职"}
    assert handler.calls == 1
    assert len(await ledger.list_records()) == 1
