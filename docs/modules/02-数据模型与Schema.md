# 数据模型与 Schema 开发规范

本模块负责定义系统的核心数据结构。所有模块都必须围绕这些 schema 交换数据，避免每个 service 自己发明字段。

## 模块职责

- 定义 Pydantic schemas。
- 定义 SQLAlchemy models。
- 定义枚举和状态机。
- 定义 API request / response 的稳定字段。
- 定义 persistence 与 runtime object 的转换边界。

## 核心实体

- `UserContext`
- `Document`
- `IngestionTask`
- `ParsedDocument`
- `DocumentChunk`
- `RetrievalHit`
- `Citation`
- `EvidenceBundle`
- `AgentRun`
- `AgentStep`
- `AgentPlan`
- `ToolDefinition`
- `ToolCall`
- `ApprovalRequest`
- `EvalCase`
- `EvalRun`
- `TraceMetadata`

## 状态枚举

`AgentRun.status`：

- `created`
- `running`
- `retrieving_evidence`
- `planning`
- `awaiting_approval`
- `resumed`
- `completed`
- `failed`
- `cancelled`

`IngestionTask.status`：

- `queued`
- `parsing`
- `chunking`
- `embedding`
- `indexing`
- `ready`
- `failed`

`ToolRiskLevel`：

- `read`
- `write`
- `admin`

## Schema 设计规则

- API 层使用 Pydantic schema。
- 数据库层使用 SQLAlchemy model。
- 业务层可以使用 Pydantic model 或 dataclass，但必须能无损转换为 API schema。
- 所有 ID 使用字符串，前缀表达类型：`doc_`、`chunk_`、`run_`、`tool_`、`appr_`。
- 时间字段使用 UTC ISO 8601。
- 分数统一使用 `0.0-1.0`，原始分数放入 `raw_score`。

## 数据库表建议

```text
documents
ingestion_tasks
document_chunks
agent_runs
agent_steps
tool_calls
approval_requests
eval_cases
eval_runs
trace_events
```

## 不做什么

- 不在 schema 中放模型调用逻辑。
- 不在 schema 中直接依赖 Milvus / Elasticsearch SDK 类型。
- 不把 citation 写成纯字符串。

## 测试要求

- `test_agent_run_status_transition_values_are_stable`
- `test_tool_definition_requires_approval_for_write_tools`
- `test_citation_serializes_source_page_section_score`
- `test_document_chunk_contains_acl_metadata`
- `test_schema_roundtrip_between_api_and_db_shape`

## 验收标准

- 所有核心字段都有类型标注。
- API response 中可以完整表达 evidence、tool_calls、approvals 和 trace metadata。
- 后续模块不需要新增重复的状态枚举。

