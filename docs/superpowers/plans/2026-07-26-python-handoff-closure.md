# Python Handoff Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 EnterpriseMind Agent Runtime 的持久化 checkpointer、落地 badcase/指标证据、README 与质量扫描收口，并保持项目独立于 Java 业务项目。

**Architecture:** LangGraph checkpointer 通过 settings 选择 memory/postgres，连接池生命周期只由 FastAPI lifespan 管理；Safety Eval 以 JSON badcase 为输入、确定性 evaluator 为断言引擎、Markdown 报告与 README 为证据出口。所有新增测试保持 fake/local first，不依赖 Docker、云 key 或外部网络。

**Tech Stack:** Python 3.12、FastAPI、LangGraph、AsyncPostgresSaver、psycopg pool、Pydantic、pytest、JSON、Markdown、vulture。

---

## File Map

- `app/services/graph/checkpointer.py`：checkpointer 工厂与连接池生命周期。
- `app/main.py`：FastAPI startup/shutdown，必须用 `try/finally` 关闭 checkpointer。
- `app/api/dependencies.py`：构造 graph runner 并注入 saver。
- `app/services/graph/graph.py`：只消费外部 saver，不管理基础设施。
- `.env.example`、`README.md`：公开配置、恢复边界与可复现指标。
- `scripts/run_landing_eval.py`：数据集校验、指标计算、原子报告输出。
- `demo_docs/badcases/*.json`：用例级和轨迹级失败夹具。
- `tests/unit/test_graph_checkpointer.py`：工厂和 manager 单元测试。
- `tests/api/test_checkpointer_lifespan.py`：异常路径仍关闭连接池。
- `tests/service/test_landing_eval.py`：数据集、指标和报告回归测试。
- `docs/evidence/landing-eval-report.md`：脚本生成的 L1 证据。
- `docs/evidence/landing-narrative-design.md`：指标口径与演示叙事。

### Task 1: Guarantee checkpointer teardown on exceptional shutdown

**Files:**
- Create: `tests/api/test_checkpointer_lifespan.py`
- Modify: `app/main.py:28-67`

- [ ] **Step 1: Write the failing lifespan test**

```python
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI

import app.api.dependencies as dependencies
import app.main as app_main


@pytest.mark.asyncio
async def test_lifespan_tears_down_postgres_checkpointer_when_app_body_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeManager:
        async def setup(self) -> None:
            calls.append("setup")

        async def teardown(self) -> None:
            calls.append("teardown")

    settings = SimpleNamespace(
        app_mode="fallback",
        graph_checkpointer_backend="postgres",
    )
    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    monkeypatch.setattr(
        dependencies,
        "get_container",
        lambda: SimpleNamespace(graph_checkpointer=FakeManager()),
    )

    with pytest.raises(RuntimeError, match="boom"):
        async with app_main.lifespan(FastAPI()):
            raise RuntimeError("boom")

    assert calls == ["setup", "teardown"]
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\api\test_checkpointer_lifespan.py -q -p no:cacheprovider`

Expected: FAIL because `teardown` is skipped when the exception is thrown into the async context manager at `yield`.

- [ ] **Step 3: Put shutdown operations in `finally`**

```python
    try:
        yield
    finally:
        if checkpointer_manager is not None:
            await checkpointer_manager.teardown()
            logger.info("graph_checkpointer_shutdown")

        if settings.app_mode == "full":
            from app.db.session import close_db

            await close_db()
            logger.info("full_mode_shutdown")
```

- [ ] **Step 4: Run checkpointer tests and confirm GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_graph_checkpointer.py tests\api\test_checkpointer_lifespan.py tests\service\test_langgraph.py -q -p no:cacheprovider`

Expected: all selected tests PASS.

- [ ] **Step 5: Commit the checkpointer implementation**

```powershell
git add app/api/dependencies.py app/config.py app/main.py app/services/graph/checkpointer.py app/services/graph/graph.py tests/api/test_checkpointer_lifespan.py tests/service/test_langgraph.py tests/unit/test_graph_checkpointer.py pyproject.toml uv.lock
git commit -m "fix: 持久化 LangGraph checkpointer 生命周期"
```

### Task 2: Document the checkpointer configuration contract

**Files:**
- Create: `tests/unit/test_runtime_configuration_docs.py`
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Write a failing documentation contract test**

```python
from pathlib import Path


def test_env_example_documents_graph_checkpointer_configuration() -> None:
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "GRAPH_CHECKPOINTER_BACKEND=memory" in content
    assert "GRAPH_CHECKPOINTER_POSTGRES_URL=" in content


def test_readme_explains_checkpoint_event_store_projection_boundary() -> None:
    content = Path("README.md").read_text(encoding="utf-8")

    assert "Checkpoint、Event Store 与 Projection" in content
    assert "GRAPH_CHECKPOINTER_BACKEND=postgres" in content
    assert "checkpoint 只保存执行位置" in content
```

- [ ] **Step 2: Run the tests and confirm RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_runtime_configuration_docs.py -q -p no:cacheprovider`

Expected: FAIL because `.env.example` and README do not yet expose the new variables and boundary text.

- [ ] **Step 3: Add the exact environment variables**

Add after `POSTGRES_URL` in `.env.example`:

```dotenv
# LangGraph checkpoint：memory 适合 fallback/测试；postgres 用于跨进程审批恢复。
GRAPH_CHECKPOINTER_BACKEND=memory
# 留空时复用 POSTGRES_URL；也可为 checkpoint 单独配置 psycopg 连接串。
GRAPH_CHECKPOINTER_POSTGRES_URL=
```

- [ ] **Step 4: Add the README boundary section**

```markdown
## Checkpoint、Event Store 与 Projection

- LangGraph checkpoint 只保存执行位置；默认 `GRAPH_CHECKPOINTER_BACKEND=memory`。
- 跨进程恢复设置 `GRAPH_CHECKPOINTER_BACKEND=postgres`，连接串优先读取 `GRAPH_CHECKPOINTER_POSTGRES_URL`，为空时复用 `POSTGRES_URL`。
- Event Store 保存不可变业务事实，Projection 服务查询/UI；两者不由 checkpoint 替代。
- PostgreSQL saver 在 FastAPI lifespan 内建表、打开和关闭连接池，单元测试仍不依赖数据库。
```

- [ ] **Step 5: Run the documentation tests and commit**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_runtime_configuration_docs.py -q -p no:cacheprovider`

Expected: 2 tests PASS.

```powershell
git add .env.example README.md tests/unit/test_runtime_configuration_docs.py
git commit -m "docs: 说明持久化 checkpoint 配置边界"
```

### Task 3: Validate badcase datasets before calculating metrics

**Files:**
- Create: `tests/service/test_landing_eval.py`
- Modify: `scripts/run_landing_eval.py`

- [ ] **Step 1: Write failing dataset validation tests**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_landing_eval import LandingEvalDataError, load_case_records, validate_dataset


def test_load_case_records_rejects_missing_cases_array(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"dataset": "broken"}), encoding="utf-8")

    with pytest.raises(LandingEvalDataError, match="cases must be a list"):
        load_case_records(path)


def test_validate_dataset_requires_three_cases_per_required_failure_mode() -> None:
    case_records = [
        {"id": "inj-1", "violation_type": "prompt_injection"},
        {"id": "inj-2", "violation_type": "prompt_injection"},
    ]

    with pytest.raises(LandingEvalDataError, match="prompt_injection requires at least 3"):
        validate_dataset(case_records, [])
```

- [ ] **Step 2: Run the tests and confirm RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\service\test_landing_eval.py -q -p no:cacheprovider`

Expected: import error because the validation API does not exist.

- [ ] **Step 3: Implement typed validation**

```python
class LandingEvalDataError(ValueError):
    """Badcase dataset does not satisfy the landing-eval contract."""


REQUIRED_MINIMUMS: dict[str, int] = {
    "prompt_injection": 3,
    "unauthorized_retrieval": 3,
    "ungrounded_answer": 3,
    "duplicate_write": 3,
    "approval_bypass": 3,
    "cost_runaway": 3,
    "crash_recovery": 3,
}


def load_case_records(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    records = payload.get("cases")
    if not isinstance(records, list):
        raise LandingEvalDataError(f"{path}: cases must be a list")
    if any(not isinstance(record, dict) for record in records):
        raise LandingEvalDataError(f"{path}: every case must be an object")
    ids = [str(record.get("id", "")) for record in records]
    if any(not case_id for case_id in ids):
        raise LandingEvalDataError(f"{path}: every case requires a non-empty id")
    if len(ids) != len(set(ids)):
        raise LandingEvalDataError(f"{path}: duplicate case id detected")
    return records


def validate_dataset(
    case_records: list[dict[str, Any]],
    trajectory_records: list[dict[str, Any]],
) -> None:
    counts: dict[str, int] = {}
    for record in [*case_records, *trajectory_records]:
        violation_type = str(record.get("violation_type", ""))
        counts[violation_type] = counts.get(violation_type, 0) + 1
    for violation_type, minimum in REQUIRED_MINIMUMS.items():
        actual = counts.get(violation_type, 0)
        if actual < minimum:
            raise LandingEvalDataError(
                f"{violation_type} requires at least {minimum} cases; found {actual}"
            )
```

- [ ] **Step 4: Route `main()` through validation and clear error handling**

```python
    try:
        case_records = load_case_records(safety_path)
        traj_records = load_case_records(trajectory_path)
        validate_dataset(case_records, traj_records)
    except (LandingEvalDataError, json.JSONDecodeError, OSError) as exc:
        print(f"[landing-eval] ERROR: {exc}", file=sys.stderr)
        return 2
```

- [ ] **Step 5: Run the focused tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests\service\test_landing_eval.py -q -p no:cacheprovider`

Expected: validation tests PASS.

### Task 4: Make metric/report generation regression-safe

**Files:**
- Modify: `tests/service/test_landing_eval.py`
- Modify: `scripts/run_landing_eval.py`
- Modify: `README.md`
- Regenerate: `docs/evidence/landing-eval-report.md`

- [ ] **Step 1: Add exact metric and report assertions**

```python
from scripts.run_landing_eval import compute_metrics, render_markdown, run_safety_cases, run_trajectory_cases


def test_repository_badcases_produce_expected_reproducible_metrics() -> None:
    case_records = load_case_records(Path("demo_docs/badcases/safety_cases.json"))
    trajectory_records = load_case_records(Path("demo_docs/badcases/trajectory_cases.json"))
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
    trajectory_records = load_case_records(Path("demo_docs/badcases/trajectory_cases.json"))
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
```

- [ ] **Step 2: Run the tests and confirm RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\service\test_landing_eval.py -q -p no:cacheprovider`

Expected: report target/boundary assertion FAIL because the current report points to `docs/drafts/README-v2-draft.md`.

- [ ] **Step 3: Correct the report text and use atomic output replacement**

```python
def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
```

Replace the mapping introduction with:

```python
lines.append("下表是写入 `README.md` 验收指标段落的可复算数值：")
lines.append("- 证据强度：L1 确定性轨迹重放，不是线上生产统计。")
```

Use `write_text_atomic(output_path, report)` and the same helper for optional JSON output.

- [ ] **Step 4: Add the README metric section using generated values**

```markdown
## 可复现的治理指标

本地确定性 badcase 重放包含 20 条用例级样本和 11 条轨迹级样本；它证明治理断言与覆盖面，不代表线上生产流量统计。

| 指标 | before | after |
| --- | ---: | ---: |
| 提示注入拦截率（已知中文改写缺口单列） | 0.0% | 100.0% |
| 越权检索拦截率 | 0.0% | 100.0% |
| 引用完整率 | 0.0% | 100.0% |
| 审批拦截率 | 0.0% | 100.0% |
| 重复副作用发生率（越低越好） | 100.0% | 0.0% |
| 崩溃恢复成功率 | 0.0% | 100.0% |

复现：`.venv/Scripts/python.exe scripts/run_landing_eval.py`。完整口径见 `docs/evidence/landing-eval-report.md`，已知缺口 `bc_inj_005` 不计入 after 头条指标。
```

- [ ] **Step 5: Regenerate evidence, run tests, and commit**

Run: `.\.venv\Scripts\python.exe scripts\run_landing_eval.py`

Expected: exit 0; 20 case-level and 11 trajectory-level cases; detection rate 100%.

Run: `.\.venv\Scripts\python.exe -m pytest tests\service\test_landing_eval.py tests\service\test_agent_safety_eval.py -q -p no:cacheprovider`

Expected: all selected tests PASS.

```powershell
git add demo_docs/badcases docs/evidence/landing-eval-report.md docs/evidence/landing-narrative-design.md README.md scripts/run_landing_eval.py tests/service/test_landing_eval.py
git commit -m "feat: 补全可复现的 Agent 治理评测证据"
```

### Task 5: Run and record the optional P3 dead-code audit

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `docs/evidence/dead-code-scan-2026-07-26.md`

- [ ] **Step 1: Add the reproducible dev dependency**

Add to `[dependency-groups].dev`:

```toml
"vulture>=2.14",
```

- [ ] **Step 2: Refresh the lock and install the dev environment**

Run: `uv lock`

Expected: `uv.lock` contains `vulture` without changing runtime dependencies.

Run: `uv sync --dev`

Expected: `.venv\Scripts\python.exe -m vulture --version` exits 0.

- [ ] **Step 3: Run the scan without deleting code**

Run: `.\.venv\Scripts\python.exe -m vulture app --min-confidence 80`

Expected: exit 0 when no findings or exit 3 when findings exist; both are valid audit outcomes.

- [ ] **Step 4: Write the evidence report**

```markdown
# Python 死代码扫描（2026-07-26）

- 命令：`.venv/Scripts/python.exe -m vulture app --min-confidence 80`
- 范围：`app/`
- 原则：FastAPI dependency、Pydantic model、protocol adapter、插件/反射入口先按误报复核，不自动删除。

## 结论

本轮只移除同时满足“仓库内零引用、非框架入口、非公开 Protocol、现有全量测试覆盖”的符号。其余结果按框架入口或保留扩展点分类，并在下方记录 vulture 原始输出与逐项判断。
```

Append the exact command output and a decision for every finding. If no symbol satisfies all deletion conditions, state that no production code was removed.

- [ ] **Step 5: Commit the scan tooling and report**

```powershell
git add pyproject.toml uv.lock docs/evidence/dead-code-scan-2026-07-26.md
git commit -m "chore: 增加 Python 死代码审计证据"
```

### Task 6: Final Python verification, cleanup, and push

**Files:**
- Verify all tracked Python deliverables.
- Remove ignored runtime artifacts only.

- [ ] **Step 1: Run the full test suite**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`

Expected: all non-integration/non-E2E tests PASS; exact count is reported rather than hard-coded.

- [ ] **Step 2: Run quality and compilation gates**

Run: `.\.venv\Scripts\python.exe scripts\quality_gate.py`

Expected: quality gate PASS.

Run: `.\.venv\Scripts\python.exe -m compileall -q app tests scripts`

Expected: exit 0.

Run: `.\.venv\Scripts\python.exe scripts\run_landing_eval.py`

Expected: exit 0 and regenerated report matches README values.

- [ ] **Step 3: Remove only the named ignored artifacts**

Resolve and verify each target is directly under `D:\Code\pythonproject`, then remove `.coverage`, `.pytest_cache`, `runtime_storage`, `runtime_test_files`, and `runtime_uv_cache`. Do not remove `.venv`, `.uv-cache`, `storage`, or user documents.

- [ ] **Step 4: Inspect final status and whitespace**

Run: `git diff --check`

Expected: no whitespace errors.

Run: `git status --short`

Expected: no unintended or generated runtime files; all required source/evidence changes are committed.

- [ ] **Step 5: Push the existing branch**

Run: `git push origin codex/enterprise-agent-runtime-v2-pr`

Expected: remote branch advances to the local HEAD.
