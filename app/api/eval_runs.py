"""
评测端点。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import ServiceContainer, get_container
from app.api.schemas import EvalRunRequest, EvalRunResponse, SafetyEvalRunRequest
from app.schemas.safety import SafetyEvalCase, SafetyEvalReport
from app.services.evaluation.safety_eval import AgentSafetyEvaluator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/runs", response_model=EvalRunResponse)
async def create_eval_run(
    body: EvalRunRequest,
    container: ServiceContainer = Depends(get_container),
) -> EvalRunResponse:
    eval_run = await container.eval_runner.run(dataset_path=body.dataset_path)

    return EvalRunResponse(
        run_id=eval_run.id,
        status=eval_run.status,
        metrics=eval_run.metrics,
    )


@router.post("/safety", response_model=SafetyEvalReport)
async def create_safety_eval_run(
    body: SafetyEvalRunRequest,
) -> SafetyEvalReport:
    """执行 deterministic Agent Safety Eval。"""
    evaluator = AgentSafetyEvaluator()
    cases = (
        [SafetyEvalCase.model_validate(case) for case in body.cases]
        if body.cases
        else evaluator.default_cases()
    )
    return evaluator.evaluate(cases)
