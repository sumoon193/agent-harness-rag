"""冻结评测报告类型。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class DimensionMetric:
    dimension: str
    count: int
    avg_latency_ms: float
    total_cost: float


@dataclass(frozen=True)
class EvalReport:
    report_id: str
    dimensions: tuple[DimensionMetric, ...]
    signature: str

    def dimension(self, name: str) -> DimensionMetric:
        for item in self.dimensions:
            if item.dimension == name:
                return item
        raise KeyError(name)


def _signature(dimensions: tuple[DimensionMetric, ...]) -> str:
    canonical = json.dumps(
        [[d.dimension, d.count, d.avg_latency_ms, d.total_cost] for d in dimensions],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
