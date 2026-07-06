# 可观测性与 Trace 开发规范

本模块负责记录 AI 应用运行过程，支持调试、评测和问题复现。

## 模块职责

- OpenTelemetry tracer 初始化。
- Phoenix / OpenInference 集成。
- 自定义 span。
- Trace metadata 标准化。
- 错误和指标记录。
- Eval run 与 trace 关联。

## Span 类型

- `agent.run`
- `agent.step`
- `retrieval.search`
- `retrieval.rerank`
- `llm.call`
- `embedding.call`
- `tool.call`
- `approval.wait`
- `guardrail.check`
- `eval.run`

## 必备属性

每个 span 至少记录：

- `run_id`
- `user_id`
- `tenant_id`
- `step_name`
- `status`
- `duration_ms`
- `error_type`
- `model_name`
- `token_input`
- `token_output`

敏感字段必须脱敏。

## Trace 树

```text
AgentRun
  -> Intent
  -> QueryRewrite
  -> Retrieval
     -> DenseSearch
     -> BM25Search
     -> RRF
     -> Rerank
  -> Planning
  -> Approval
  -> ToolCall
  -> Answer
  -> Eval
```

## Phoenix 集成

- full mode 发送 OTLP traces 到 Phoenix。
- fallback mode 使用本地 structured logs。
- trace id 返回给 API 和前端。

## 不做什么

- 不在 trace 中存储完整敏感文档。
- 不把可观测性代码散落在所有业务函数中，优先使用 wrapper / decorator。
- 不让 trace 失败影响主链路。

## 测试要求

- `test_trace_id_created_for_agent_run`
- `test_retrieval_span_records_scores`
- `test_tool_span_records_approval_id`
- `test_sensitive_fields_are_redacted`
- `test_observability_failure_does_not_fail_request`

## 验收标准

- 每次 Agent Run 都能定位 trace。
- 前端能展示 step tree。
- 评测结果可以关联具体 run 和 trace。

