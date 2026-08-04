"""冻结评测器：从指标样本计算四维可复核报告。"""

from __future__ import annotations

from app.devmate.eval.report import DimensionMetric, EvalReport, _signature
from app.devmate.observability import MetricSample

DIMENSIONS = ("diagnosis", "sandbox", "approval", "side_effect")


class Evaluator:
    def evaluate(self, samples: tuple[MetricSample, ...]) -> EvalReport:
        dimensions: list[DimensionMetric] = []
        for dimension in DIMENSIONS:
            latency = [
                sample.value
                for sample in samples
                if sample.metric == f"{dimension}.latency_ms"
            ]
            cost = [
                sample.value
                for sample in samples
                if sample.metric == f"{dimension}.cost"
            ]
            count = len(latency)
            avg_latency = sum(latency) / count if latency else 0.0
            dimensions.append(
                DimensionMetric(
                    dimension=dimension,
                    count=count,
                    avg_latency_ms=avg_latency,
                    total_cost=sum(cost),
                )
            )
        frozen = tuple(dimensions)
        return EvalReport(
            report_id="eval-report",
            dimensions=frozen,
            signature=_signature(frozen),
        )
