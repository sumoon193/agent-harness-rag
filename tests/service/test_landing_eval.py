"""落地叙事 badcase、指标和报告的回归测试。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_landing_eval import (
    LandingEvalDataError,
    compute_metrics,
    load_case_records,
    render_markdown,
    run_safety_cases,
    run_trajectory_cases,
    validate_dataset,
)


def test_load_case_records_rejects_missing_cases_array(tmp_path: Path) -> None:
    """数据集缺少 cases 数组时必须给出清晰错误。"""
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"dataset": "broken"}), encoding="utf-8")

    with pytest.raises(LandingEvalDataError, match="cases must be a list"):
        load_case_records(path)


def test_validate_dataset_requires_three_cases_per_required_failure_mode() -> None:
    """交接要求中的每种失败模式至少保留三条样本。"""
    case_records = [
        {"id": "inj-1", "violation_type": "prompt_injection"},
        {"id": "inj-2", "violation_type": "prompt_injection"},
    ]

    with pytest.raises(
        LandingEvalDataError,
        match="prompt_injection requires at least 3",
    ):
        validate_dataset(case_records, [])


def test_repository_badcases_produce_expected_reproducible_metrics() -> None:
    case_records = load_case_records(Path("demo_docs/badcases/safety_cases.json"))
    trajectory_records = load_case_records(
        Path("demo_docs/badcases/trajectory_cases.json")
    )
    metrics = compute_metrics(
        run_safety_cases(case_records),
        run_trajectory_cases(trajectory_records),
    )

    assert metrics["METRIC_INJECTION_INTERCEPT_BEFORE"] == 0.0
    assert metrics["METRIC_INJECTION_INTERCEPT_AFTER"] == 100.0
    assert metrics["METRIC_DUP_SIDE_EFFECT_RATE_BEFORE"] == 100.0
    assert metrics["METRIC_DUP_SIDE_EFFECT_RATE_AFTER"] == 0.0
    assert metrics["METRIC_TRAJECTORY_DETECTION_RATE"] == 100.0


def test_report_names_readme_as_the_public_metric_target() -> None:
    case_records = load_case_records(Path("demo_docs/badcases/safety_cases.json"))
    trajectory_records = load_case_records(
        Path("demo_docs/badcases/trajectory_cases.json")
    )
    case_outcomes = run_safety_cases(case_records)
    trajectory_outcomes = run_trajectory_cases(trajectory_records)
    report = render_markdown(
        case_outcomes,
        trajectory_outcomes,
        compute_metrics(case_outcomes, trajectory_outcomes),
    )

    assert "README.md" in report
    assert "确定性轨迹重放，不是线上生产统计" in report
    assert "bc_inj_005" in report
