# 指标与简历证据

## 目标

把 Harness 深化能力转化为可复现的工程证据和简历表达。

## 指标口径

| 能力 | 指标 | 说明 |
| --- | --- | --- |
| Loop Engineering | repair 触发次数、成功修复率 | 基于固定评测样例 |
| MCP Adapter | schema 校验失败拦截数、写工具审批拦截数 | fake MCP server 可复现 |
| Safety Eval | 每类风险通过率 | 不依赖云模型 |
| Timeline | run 事件完整率 | 必须覆盖关键阶段 |
| Citation | 引用有效率 | citations 必须能对应 evidence |

## 证据文件建议

- `docs/agent-harness-deepening/evidence/loop-engineering-eval.md`
- `docs/agent-harness-deepening/evidence/mcp-adapter-test.md`
- `docs/agent-harness-deepening/evidence/safety-eval-report.md`
- `docs/agent-harness-deepening/evidence/artifact-timeline-demo.md`

## 简历候选表达

- 在自研 Agent Harness 中引入 Loop Engineering，将规划、执行、观察、反思、修复沉淀为可审计事件流，提升 Agent 失败复盘和自动修复能力。
- 设计 MCP 风格工具适配层，将外部工具统一纳入 schema 校验、审批、权限和审计体系，避免工具接入绕过 Harness 治理。
- 构建 Agent Safety Eval 体系，覆盖越权检索、提示注入、引用缺失和写工具误调用等风险，并输出可追踪评测报告。

## 面试追问准备

- Loop Engineering 和普通 ReAct prompt 的区别是什么？
- MCP adapter 为什么不能直接调用工具？
- 安全评测如何避免依赖模型随机性？
- Timeline 和 trace 的区别是什么？
- 指标是如何构造样本和复现的？
