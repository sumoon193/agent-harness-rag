# EnterpriseMind Agent Runtime V2 架构

## 边界

平台层只使用 `Case`、`Run`、`Event`、`Tool`、`Approval`、`Timer`、`Memory`、`Skill`、`Artifact`。HR 逻辑位于 Reference Application 的 Skill、policy resource、adapter 和 eval dataset。

## 写路径

```text
Command(expected_version, command_id)
  -> acquire run lease / fencing token
  -> append domain event + outbox in one transaction
  -> update idempotent Case projection
  -> publish/consume outbox with claim + ack
  -> stream by persistent sequence cursor
```

## 审批恢复

```text
tool.call_prepared
  -> approval.requested(subject_hash, evidence, policy, manifest, expiry)
  -> checkpoint / waiting_approval
  -> human decision
  -> re-authorize + evidence freshness
  -> reserve SideEffect Ledger
  -> external call
       success -> cache result
       unknown -> reconciliation required
  -> tool.executed
  -> durable timer / next case stage
```

## 数据职责

| 数据 | 权威来源 | 用途 |
| --- | --- | --- |
| 执行位置 | LangGraph checkpoint | interrupt/resume |
| 业务事实 | Runtime Event Store | 审计、回放、Timeline |
| 查询模型 | Case projection | API/UI 队列和详情 |
| 外部写入 | SideEffect Ledger | effectively-once/reconciliation |
| 延迟动作 | Durable Timer | SLA、提醒、审批过期 |
| 制度事实 | DocumentVersion + indexes | evidence/citations/freshness |

## 一致性

- aggregate sequence 与 expected version 提供乐观并发控制。
- command id 防止同一业务命令重复追加事件。
- event hash chain 用于发现顺序或内容篡改。
- event/outbox 同事务，projection 和 publisher 必须幂等。
- API lease 串行化同一 Case 的命令并签发单调 fencing token；当前 reference workflow 以 optimistic version 作为最终旧写保护，接入长耗时 worker 时应把 fencing token 下推到写 adapter 强制校验。
- 外部系统不属于本地事务，使用 ledger 明确表达 `unknown`。

## 协议

- MCP：本地 HTTP JSON-RPC，版本 `2025-11-25`，覆盖 initialize/tools/resources/prompts。
- A2A：AgentCard、Message、Task、Artifact；Policy Research peer 只读。
- 所有协议 adapter 必须降级到 deterministic fake，不能绕过 Harness。

## 可观测性

- trace/span 关联 `case_id/run_id/event_id`。
- Event Store 指标：event total、outbox backlog/published。
- 治理指标：approval wait/stuck、human intervention、side effect、安全零值。
- 协议指标：MCP/A2A success/failure。
- 恢复指标：projection lag、rebuild success、timer claim。

## 失败模型

| 失败 | 处理 |
| --- | --- |
| version conflict | 拒绝命令，客户端刷新 projection 后重试 |
| worker crash | lease 过期接管，checkpoint/event replay 恢复 |
| outbox publisher crash | claim 超时回收，幂等重投 |
| approval expired/revoked | 拒绝执行并生成新 revision |
| evidence stale | 只读 A2A 重新研究，更新计划和审批 |
| tool timeout after send | ledger 标记 unknown，进入 reconciliation |
| context overflow | 压缩安全前缀，pin 治理事件，验证 invariant |

## 非目标

- 真实 HRIS、工资、考勤和完整 HR SaaS。
- 完整生产 IAM/RBAC、Kubernetes、Kafka、Temporal。
- GraphRAG 主链路和远程 MCP 生态依赖。
