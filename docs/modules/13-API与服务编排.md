# API 与服务编排开发规范

本模块负责把领域能力暴露为稳定 HTTP API，并协调多个 service 完成一次用户请求。

## 模块职责

- FastAPI route。
- Request / response schema 映射。
- Service dependency wiring。
- SSE streaming。
- Error response。
- API versioning。
- 跨模块应用服务编排。

## API 分组

```text
app/api/
  health.py
  documents.py
  ingestions.py
  agent_runs.py
  approvals.py
  eval_runs.py
```

对应 service：

```text
app/services/
  document_service.py
  ingestion_service.py
  agent_run_service.py
  approval_service.py
  eval_service.py
```

## Route 规则

- route 不写业务逻辑。
- route 只做鉴权上下文解析、参数校验、调用 service、返回 response。
- 所有错误使用统一 error shape。
- 所有 response 都有稳定字段，不直接返回 ORM model。

## V1 API

- `POST /documents`
- `GET /ingestions/{task_id}`
- `POST /agent-runs`
- `GET /agent-runs/{run_id}`
- `GET /agent-runs/{run_id}/stream`
- `POST /agent-runs/{run_id}/approvals/{approval_id}`
- `POST /eval/runs`
- `GET /health`

## Error Shape

```json
{
  "error": {
    "code": "approval_not_found",
    "message": "审批请求不存在或已处理",
    "request_id": "req_xxx",
    "details": {}
  }
}
```

## SSE 规范

事件必须包含：

- `event`
- `run_id`
- `step_name`
- `payload`
- `created_at`

断线重连时，前端可通过 `GET /agent-runs/{run_id}` 获取当前状态。

## 不做什么

- 不在 route 中直接访问 Milvus、Elasticsearch 或 LLM。
- 不让前端传入服务端可推导的权限字段。
- 不把异常堆栈直接返回给用户。

## 测试要求

- `test_create_agent_run_returns_run_id`
- `test_get_agent_run_returns_steps_evidence_approvals`
- `test_submit_approval_resumes_run`
- `test_sse_stream_emits_ordered_events`
- `test_api_error_shape_is_stable`
- `test_route_does_not_expose_internal_exception`

## 验收标准

- API 能驱动标准 demo 完整流程。
- 前端无需理解内部领域对象即可渲染状态。
- 所有失败都能返回可读且稳定的错误码。

