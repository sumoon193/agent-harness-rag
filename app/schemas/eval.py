"""
评测相关 Schema。
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    """
    评测用例。

    单个问题-答案对，用于 RAGAS 评测。
    """
    id: str = Field(description="用例 ID，前缀 eval_")
    question: str = Field(description="问题")
    answer: str = Field(description="标准答案")
    contexts: list[str] = Field(
        description="相关上下文列表"
    )
    ground_truth_docs: list[str] = Field(
        default_factory=list,
        description="相关文档名称列表"
    )
    ground_truth_sections: list[str] = Field(
        default_factory=list,
        description="相关章节列表"
    )
    expected_tools: list[str] = Field(
        default_factory=list,
        description="预期调用的工具列表"
    )
    requires_approval: bool = Field(
        default=False,
        description="是否需要审批"
    )

    model_config = {"from_attributes": True}


class EvalRun(BaseModel):
    """
    评测运行。

    一次评测任务的元数据和结果。
    """
    id: str = Field(description="运行 ID")
    dataset_name: str = Field(description="数据集名称")
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="评测指标（context_precision, context_recall, faithfulness, answer_relevancy）"
    )
    status: str = Field(
        default="pending",
        description="运行状态（pending/running/completed/failed）"
    )
    started_at: datetime | None = Field(
        default=None,
        description="开始时间（UTC）"
    )
    completed_at: datetime | None = Field(
        default=None,
        description="完成时间（UTC）"
    )

    model_config = {"from_attributes": True}


class EvalResult(BaseModel):
    """
    评测结果。

    单个用例的评测指标。
    """
    case_id: str = Field(description="用例 ID")
    metrics: dict[str, float] = Field(
        description="评测指标"
    )

    model_config = {"from_attributes": True}
