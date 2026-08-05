# Python 项目交接收口设计

## 目标

严格完成 `D:/Code/HANDOFF-REMAINING-WORK.md` 中属于 EnterpriseMind Agent Runtime 的 P0、P1 与验收要求，并执行 P3 只读死代码扫描。项目继续以 HR Shared Service 为独立 Reference Application，不引入优惠券补偿第二参考域，也不与 Java 项目建立代码依赖。

## 范围

### 纳入范围

- 收口 LangGraph checkpointer 的 memory/postgres 配置、异步生命周期、测试与文档。
- 清理交接文档列出的运行垃圾，并保持用户源码改动不受影响。
- 完成 badcase 数据集、before/after 评测脚本、落地叙事设计、评测报告和 README 指标证据。
- 为数据集结构、指标计算和报告生成补回归测试，避免证据文件与实现漂移。
- 对 Python 源码执行死代码扫描，形成分类结论；只修复与本轮相关且可由测试证明安全的问题。
- 复核 `D:/Code/newproject/docs/interview-prep-dual-project.md` 中 Python 项目的讲述和代码锚点，但不把两个项目描述成同一系统。

### 不纳入范围

- 不实现优惠券补偿 Skill、adapter 或第二业务域。
- 不接真实 HR 系统，不扩展完整 IAM、GraphRAG 或远程 MCP 生态。
- 不把云模型、Docker 或外部中间件作为单元测试前置条件。
- 不把确定性重放指标描述成线上生产统计。

## 架构与数据流

### Checkpointer

`Settings` 选择 `memory` 或 `postgres` 后端。memory 使用 `MemorySaver`，无需生命周期操作；postgres 使用 `AsyncPostgresSaver` 和延迟打开的 `AsyncConnectionPool`。构造必须发生在运行中的事件循环内，FastAPI lifespan 在启动阶段打开连接池并执行 saver setup，在关闭阶段释放连接池。`create_agent_graph` 只接收 `BaseCheckpointSaver`，不负责创建或关闭基础设施。

LangGraph checkpoint 只保存执行位置。长期业务事实仍由 Event Store 保存，查询视图仍由 Projection 保存，三者职责不得混写。

### 落地评测证据链

`demo_docs/badcases/*.json` 是输入事实，`AgentSafetyEvaluator` 是确定性断言引擎，`scripts/run_landing_eval.py` 负责加载相同样本并分别运行 governance-off 重放与完整 Harness 重放，最终生成 `docs/evidence/landing-eval-report.md`。README 只引用报告中可复算的 L1 指标，并明确 L1 是确定性轨迹重放而不是线上流量统计。

已知缺口必须保留，例如当前 PromptGuard 对部分中文改写注入识别不足。报告同时展示通过项和已知缺口，禁止为了得到 100% 指标而删除失败样本。

### 项目独立性

Python 项目独立证明通用 Agent Runtime、RAG 证据层、长流程恢复和 Safety Eval。与 Java 项目的关系仅存在于求职材料的并列展示中，不共享源码、业务 adapter、数据集或运行时配置。

## 错误处理与边界

- 显式选择 postgres 且依赖缺失时，返回包含安装指引的清晰错误。
- postgres saver 在无事件循环的同步上下文构造时，返回明确的生命周期错误。
- memory 后端 setup/teardown 必须幂等且无外部依赖。
- 评测数据缺字段、类别未知或轨迹结构非法时，脚本以非零状态退出并指出具体 case。
- 报告输出采用临时内容生成后原子替换，避免失败时留下半份指标报告。

## 测试与验收

- checkpointer 工厂、配置回退、依赖缺失、同步上下文错误、setup/teardown 幂等测试。
- graph 注入外部 saver 的服务测试。
- badcase 每个要求类别至少三条的结构测试。
- before/after 指标公式和已知缺口的回归测试。
- 完整命令：`pytest -q -p no:cacheprovider`、`scripts/quality_gate.py`、`scripts/run_landing_eval.py`、`compileall`。
- README 中的指标、样本数、复现命令必须与生成报告一致。
- 工作树不得残留 `.coverage`、`.pytest_cache`、`runtime_storage`、`runtime_test_files`、`runtime_uv_cache`。

## 交付方式

先提交 checkpointer 修复，再提交落地证据与必要的扫描结论。每个提交只暂存本轮对应文件；通过全量验证后推送当前分支 `codex/enterprise-agent-runtime-v2-pr`。
