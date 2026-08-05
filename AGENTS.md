# DevMate 项目 Agent 入口

本仓库是 DevMate 与 EnterpriseMind Agent Runtime 的生产代码仓库。进入项目后，必须先读取中央治理入口，再按本文件和 `.agent-governance/AGENT-ENTRY.md` 执行当前任务。

## 项目定位

DevMate 面向 CI 失败诊断与受控修复流程。系统以 RAG 作为可信证据层，以 Agent Harness 作为执行治理层，并以 Runtime Kernel 保存长期 Case、Event Store、Outbox、Projection、Lease、SideEffect Ledger 和 Durable Timer。

HR Shared Service 是 Reference Application，不是平台边界。GitHub webhook、诊断、RepairPlan、Sandbox、审批和 PR 副作用通过 typed contract 与可恢复状态链连接。

## 必读顺序

1. 中央仓库 `AGENTS.md` 与中央治理协议。
2. `.agent-governance/AGENT-ENTRY.md`。
3. `.agent-governance/manifest.json`、`implementation-plan.md`、`module-contracts.json`。
4. 当前分支对应的 `.agent-governance/tasks/*.json`。
5. `开发规划.md`、`docs/modules/00-模块规范总览.md`、`docs/CODING_STANDARDS.md`。
6. 当前任务相关模块文档与 `docs/DECISIONS.md`。

## 硬性约束

- 只在任务包指定分支和白名单路径内工作。
- 每项行为必须先运行失败测试，再做最小实现和完整回归。
- 禁止删除、跳过或弱化测试来制造通过。
- 禁止读取或提交 `.env`、Cookie、Token、私有日志和受限运行时数据。
- 单元测试不得依赖 Docker、云 API key 或外部网络。
- 外部依赖必须通过可注入 adapter 接入，并提供离线适配器或固定测试数据。
- API 层只做协议适配和服务编排，不承载领域状态机决策。
- ACL 必须在检索前生效；用户可见结论必须关联 citation，证据不足时保持拒答、追问或 blocked。
- 所有写副作用必须审批、幂等、审计，并处理 `UNKNOWN` 对账。
- 可以 commit 和普通 push；禁止 merge、rebase 他人分支、force-push 和自动合并。
- 当前体系仅保留工程实施、验证和运维资料。

## 工程文档

- `README.md`：项目能力、启动、API、测试和真实服务验证。
- `开发规划.md`：模块规划和实施顺序。
- `docs/architecture/enterprise-agent-runtime-v2.md`：整体架构。
- `docs/modules/`：模块契约与验收边界。
- `docs/CODING_STANDARDS.md`：编码规范。
- `docs/DECISIONS.md`：关键工程决策。
- `docs/audit/`：来源、许可证和领域耦合审计。
- `docs/devmate/release/`：发布、回滚和真实性验证。
