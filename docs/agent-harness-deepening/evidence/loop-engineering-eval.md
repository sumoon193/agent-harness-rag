# Loop Engineering 落地证据

## 落地范围

- 新增 `app/schemas/harness.py`：定义 `LoopStage`、`LoopDecision`、`LoopEvent`。
- 新增 `app/services/agent/loop_engine.py`：把 `plan / observe / reflect / repair` 固化为可审计事件。
- Loop 事件统一写入 `StepLogger`，可被 Artifact Timeline 复盘。

## 已验证行为

- 证据不足时生成 `reflection_created`，决策为 `repair`。
- citation 缺失会进入 repair，而不是输出无证据答案。
- 写工具待审批时只生成 `await_approval`，不会绕过审批执行。
- 工具失败时 repair 会保留前一次失败原因。

## 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest tests\service\test_loop_engineering.py -q -p no:cacheprovider
```

当前结果：`3 passed`。
