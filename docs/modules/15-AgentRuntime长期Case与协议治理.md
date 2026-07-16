# 模块 15：Agent Runtime 长期 Case 与协议治理

## 目标

把单轮 `AgentRun` 深化为跨轮次、跨天、可审计、可恢复的通用 Case Runtime，并用 HR 入职到转正作为 Reference Application。

## 必须满足

- Event Store append-only、sequence 单调、optimistic version、command idempotency。
- event/outbox 同事务；outbox claim 可超时回收，ack 幂等。
- Case projection 可从事件重建，full mode 使用 SQLAlchemy/PostgreSQL adapter。
- 审批绑定参数、证据、policy、manifest、revision 和 expiry。
- 写副作用进入 SideEffect Ledger；`unknown` 不得自动重试。
- Durable Timer 可被多个 scheduler 竞争但只能 claim 一次。
- Context Snapshot 不删除原事件，未决审批和失败必须 pin。
- Memory 必须有 tenant ACL、provenance、quarantine 和 forget。
- Skill 必须有来源白名单、checksum、eval gate 和 revoke。
- MCP/A2A 不得绕过 ToolRegistry、ACL、approval、ledger 和 trace。
- Safety Eval 必须扫描有序 trajectory。

## 测试

- 纯内存 fake 覆盖主语义。
- async SQLite 覆盖与 PostgreSQL 共用的 SQLAlchemy transaction/adapters。
- 单元/service/API 不依赖 Docker、云 key 或外部网络。
- E2E 覆盖创建 Case、启动、审批前无写入、批准恢复、timer 和安全指标。

## 验收

标准 Case 的 Timeline 至少包含：

```text
case.created
run.started
skill.loaded
a2a.task.completed
evidence.retrieved
plan.created
tool.call_prepared
approval.requested
context.compacted
approval.decided
tool.executed
memory.stored
timer.scheduled
```

重复审批命令不得产生第二次外部写入；服务重启后必须能从 projection 或 event replay 查询 Case。
