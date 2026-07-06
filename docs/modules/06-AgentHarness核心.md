# Agent Harness 核心开发规范

本模块负责智能体执行治理层，是项目区别于普通 RAG 的核心。

## 模块职责

- Agent Run 生命周期。
- Agent Step 记录。
- Plan-then-Execute。
- Tool Registry。
- Tool permission scope。
- Tool approval request。
- 审批后恢复执行。
- 工具结果审计。

## 核心对象

`AgentRun`：

- `run_id`
- `question`
- `user`
- `status`
- `plan`
- `steps`
- `evidence`
- `tool_calls`
- `approvals`
- `result`
- `trace_id`

`ToolDefinition`：

- `name`
- `description`
- `input_schema`
- `risk_level`
- `permission_scope`
- `requires_approval`
- `timeout_seconds`
- `idempotent`

## 状态机规则

允许状态流转：

```text
created -> running
running -> retrieving_evidence
retrieving_evidence -> planning
planning -> awaiting_approval
planning -> completed
awaiting_approval -> resumed
awaiting_approval -> cancelled
resumed -> completed
resumed -> failed
```

非法流转必须抛出业务异常并记录 step。

## V1 工具

- `policy_search`: read，不需要审批。
- `get_user_profile`: read，不需要审批。
- `generate_hr_checklist`: read，不需要审批。
- `ask_clarification`: read，不需要审批。
- `create_mock_hr_ticket`: write，必须审批。

## 审批规则

- 写入型工具必须生成 `ApprovalRequest`。
- 审批前不能执行工具。
- 审批支持 `approve`、`edit`、`reject`。
- edit 后必须记录原始参数和修改后参数。
- reject 后 Agent 可以 re-plan 或结束。

## 不做什么

- V1 不连接真实 HR 系统。
- Tool 不直接访问 FastAPI request。
- Harness 不直接拼 prompt，应调用 planner / answer service。

## 测试要求

- `test_write_tool_requires_approval_before_execution`
- `test_read_tool_executes_without_approval`
- `test_approval_resume_keeps_same_run_id`
- `test_reject_records_audit_step`
- `test_invalid_status_transition_is_rejected`
- `test_tool_registry_refuses_unregistered_tool`

## 验收标准

- 标准问题“新员工入职到转正要办哪些事项？”能产生 plan、evidence、approval 和 mock ticket result。
- 写入型工具在审批前绝不执行。
- 每次工具调用都有审计记录。

