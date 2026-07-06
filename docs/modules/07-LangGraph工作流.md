# LangGraph 工作流开发规范

本模块负责把 Agent Harness 的执行逻辑编排成可中断、可恢复、可流式输出的有状态图。

## 模块职责

- 定义 graph state。
- 定义节点函数。
- 定义路由条件。
- 接入 checkpointer。
- 实现 interrupt/resume。
- 输出 SSE events。

## State 字段

```python
class AgentGraphState(TypedDict):
    run_id: str
    thread_id: str
    user: UserContext
    question: str
    intent: str | None
    rewritten_queries: list[str]
    evidence: EvidenceBundle | None
    plan: AgentPlan | None
    pending_tool_call: ToolCall | None
    approval_decision: ApprovalDecision | None
    tool_results: list[ToolResult]
    answer: AnswerResponse | None
    errors: list[str]
```

## 节点设计

- `intent_node`
- `query_rewrite_node`
- `retrieve_node`
- `evidence_score_node`
- `plan_node`
- `approval_gate_node`
- `tool_execute_node`
- `answer_node`
- `fact_check_node`
- `finalize_node`

## 中断规则

只在以下场景使用 dynamic interrupt：

- 写入型工具待审批。
- 证据不足需要用户补充信息。
- 高风险输出需要人工确认。

中断 payload 必须 JSON-serializable，并包含：

- `run_id`
- `approval_id`
- `tool_name`
- `tool_args`
- `risk_level`
- `evidence_summary`
- `allowed_decisions`

## Checkpoint 规则

- 每个 graph run 必须传入稳定 `thread_id`。
- 测试使用 in-memory checkpointer。
- full mode 使用 PostgreSQL 或 LangGraph 支持的持久化 checkpointer。
- interrupt 前的副作用必须幂等，避免 resume 时重复执行。

## SSE 事件

- `run_started`
- `step_started`
- `step_completed`
- `evidence_found`
- `approval_required`
- `tool_executed`
- `answer_ready`
- `run_failed`

## 不做什么

- 不在 graph node 中直接访问数据库 session，全都通过 service。
- 不在 interrupt 前执行写入型工具。
- 不把 graph state 当作长期业务数据库。

## 测试要求

- `test_graph_interrupts_before_write_tool`
- `test_graph_resumes_with_same_thread_id`
- `test_graph_reject_path_does_not_execute_tool`
- `test_graph_low_confidence_routes_to_clarification`
- `test_sse_events_follow_step_order`

## 验收标准

- 一次标准 Agent Run 能暂停、审批、恢复并完成。
- 断点恢复不会重复检索或重复创建 mock ticket。
- 前端能通过 SSE 展示完整运行过程。

