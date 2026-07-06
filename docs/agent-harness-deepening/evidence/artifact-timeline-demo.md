# Artifact Timeline 落地证据

## 落地范围

- 新增 `app/services/agent/artifact_timeline.py`：从 steps、tool calls、approvals 和 result 派生复盘时间线。
- `GET /agent-runs/{run_id}` 新增 `timeline` 字段。
- Timeline 使用 `PIIRedactor` 对摘要脱敏，不保存敏感原文。

## 事件映射

- `run_created` -> `run_created`
- `evidence_retrieved` -> `evidence_retrieved`
- `plan_created` -> `plan_generated`
- `tool_approval_requested` -> `approval_requested`
- `approval_approved / approval_rejected / approval_edited` -> `approval_decided`
- `tool_executed / tool_executed_after_approval` -> `tool_executed`
- `reflection_created` -> `reflection_created`
- `repair_action_created` -> `repair_action_created`
- `run_completed` -> `answer_generated`

## 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest tests\service\test_artifact_timeline.py tests\api\test_harness_deepening_api.py::test_agent_run_detail_returns_artifact_timeline -q -p no:cacheprovider
```

当前结果：Timeline service 与 API 均通过。
