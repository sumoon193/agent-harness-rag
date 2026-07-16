"""
审批提交端点。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import ServiceContainer, get_container
from app.api.schemas import ApprovalSubmitRequest, ApprovalSubmitResponse
from app.schemas.approval import ApprovalDecision
from app.schemas.enums import ApprovalDecisionType, ApprovalStatus
from app.schemas.user import UserContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-runs", tags=["approvals"])


@router.post("/{run_id}/approvals/{approval_id}", response_model=ApprovalSubmitResponse)
async def submit_approval(
    run_id: str,
    approval_id: str,
    body: ApprovalSubmitRequest,
    container: ServiceContainer = Depends(get_container),
) -> ApprovalSubmitResponse:
    # V1 简化：审批人固定为 admin
    user_context = UserContext(
        user_id="admin_001",
        tenant_id="tenant_001",
        department_ids=["dept_hr"],
        role="admin",
        permissions=["hr.ticket.write"],
    )

    decision = ApprovalDecision(
        decision=ApprovalDecisionType(body.decision),
        edited_parameters=body.edited_parameters,
    )

    if getattr(container.settings, "agent_run_engine", "demo") == "langgraph":
        run = await container.run_manager.get_run(run_id)
        async for _ in container.graph_runner.resume(
            thread_id=run.thread_id,
            approval_decision=decision,
            user_context=user_context,
        ):
            pass

        approvals = await container.run_manager.get_run_approvals(run_id)
        approval = next(
            (
                item
                for item in approvals
                if item.supersedes_approval_id == approval_id
            ),
            next(item for item in approvals if item.id == approval_id),
        )
        return ApprovalSubmitResponse(
            approval_id=approval.id,
            status=approval.status,
            decision=approval.decision or body.decision,
        )

    approval = await container.run_manager.apply_approval_decision(
        run_id=run_id,
        approval_id=approval_id,
        approval_decision=decision,
        user_context=user_context,
    )

    run = await container.run_manager.get_run(run_id)
    previous_result = run.result or {}

    if approval.status == ApprovalStatus.APPROVED:
        tool_call = await container.run_manager.execute_approved_tool(
            run_id=run_id,
            approval_id=approval.id,
            user_context=user_context,
        )
        await container.run_manager.complete_run(
            run_id=run_id,
            result={
                **previous_result,
                "answer": "已审批并创建模拟 HR 工单，办理清单和引用来源已保留在本次 Run 中。",
                "tool_result": tool_call.result,
                "approval_required": False,
            },
        )
    elif approval.status == ApprovalStatus.REJECTED:
        await container.run_manager.mark_resumed_without_tool(
            run_id=run_id,
            reason="approval_rejected",
        )
        await container.run_manager.complete_run(
            run_id=run_id,
            result={
                **previous_result,
                "answer": "已拒绝执行写入型工具，不会创建模拟 HR 工单。",
                "tool_result": None,
                "approval_required": False,
            },
        )

    return ApprovalSubmitResponse(
        approval_id=approval.id,
        status=approval.status,
        decision=approval.decision or body.decision,
    )
