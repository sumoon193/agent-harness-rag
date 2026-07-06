# 关键决策记录

这份文档记录 EnterpriseMind Agent Harness RAG 的关键产品和技术取舍。后续如果方向变化，应先更新本文件，再更新规划和模块规范。

## D-001：项目主线是 Agent Harness + RAG

**决策：** 项目不是普通 RAG Chatbot，而是自研 Agent Harness + RAG。

**原因：** 普通 RAG 只能体现检索和回答能力，无法体现企业 agent 的执行治理。项目亮点应放在 Agent Run 生命周期、工具审批、状态恢复、ACL、审计和评测上。

**影响：** 所有模块都必须服务两个目标：RAG 提供 evidence，Harness 控制 agent 执行。

## D-002：RAG 是可信证据层，不只是上下文拼接

**决策：** RAG 层必须输出结构化 `EvidenceBundle` 和 `Citation`。

**原因：** 企业问答必须能追溯来源，不能只把检索片段塞进 prompt。

**影响：** 答案生成、工具计划和评测都必须引用 evidence；证据不足时拒答或追问。

## D-003：V1 聚焦 HR 制度流程

**决策：** V1 只做 HR 制度流程场景，包括入职、转正、报销、请假和模拟 HR 工单。

**原因：** HR 场景天然包含制度、角色、审批、流程和引用，适合展示 Agent Harness + RAG 的完整价值。

**影响：** V1 不扩展到合同审查、代码助手、DevOps 或真实办公系统。

## D-004：先 fallback，后 full mode

**决策：** 先实现 pure Python / in-memory / deterministic fake 的后端领域闭环，再接 Docker 和真实中间件。

**原因：** 如果一开始依赖 Milvus、Elasticsearch、PostgreSQL、Redis、MinIO、Celery 和云模型，开发会被环境问题拖住。

**影响：** 单元测试不能依赖 Docker、云 API key 或外部网络。所有外部系统都必须有 adapter 和 fake。

## D-005：写入型工具必须审批

**决策：** 所有写入型工具默认 `requires_approval=true`。

**原因：** 企业 agent 的核心风险不是“答错”，而是“错误执行副作用动作”。审批是 Agent Harness 和普通 RAG 的关键分界线。

**影响：** `create_mock_hr_ticket` 等工具在审批前绝不能执行；审批结果必须写入 Agent Run 和 trace。

## D-006：ACL 必须检索前生效

**决策：** 权限过滤必须在检索前生效，答案生成前再二次校验 citations。

**原因：** 如果先召回无权限内容再过滤，敏感信息仍可能进入 LLM 上下文，造成泄露。

**影响：** Milvus filter、Elasticsearch filter、EvidenceBuilder 和 AnswerService 都必须接收并执行权限约束。

## D-007：Qwen Cloud 为云端优先，模型维度不写死

**决策：** 云端 embedding 优先使用 `text-embedding-v4`，rerank 使用 `qwen3-rerank`；本地可替换为 Qwen3 / BGE 系列。

**原因：** 模型产品和维度会变化，文档和 schema 不应写死某个固定维度。

**影响：** 使用 `settings.EMBEDDING_DIM`，由配置决定 Milvus vector dim。

## D-008：Docling 主解析，MinerU 增强

**决策：** Docling 作为主解析 adapter，MinerU 作为复杂 PDF、扫描件和版面分析增强选项。

**原因：** Docling 支持多格式统一转换，适合作为标准 parser；MinerU 在复杂 PDF 和版面场景有补充价值。

**影响：** Parser Registry 必须支持多 parser 路由和 fallback。

## D-009：GraphRAG 和 MCP 是 V2

**决策：** V1 不实现完整 GraphRAG / LightRAG 和 MCP Server，只预留边界。

**原因：** V1 首要目标是跑通 Agent Harness + RAG 主链路。过早引入 GraphRAG / MCP 会拉大范围。

**影响：** 相关设计放入 `docs/modules/12-V2扩展GraphRAG与MCP.md`，不阻塞 V1。

## D-010：前端是控制台，不是营销页

**决策：** 前端做操作型控制台，当前实现采用 Vue 3 + Element Plus，第一屏展示 Agent Run、approval、evidence 和 trace，并提供文档入库与评测入口。

**原因：** 项目需要演示真实工作流，而不是宣传页面。

**影响：** UI 设计优先信息密度、状态可见性和操作闭环。

## D-011：评测与可观测必须进入主叙事

**决策：** RAGAS 和 Phoenix / OpenTelemetry 是项目核心亮点之一，不只是附属工具。

**原因：** RAG 和 Agent 系统不能靠主观感觉调参，必须能用指标和 trace 排查问题。

**影响：** 每个 Agent Run 应能关联 trace；评测要覆盖 RAG 指标和 agent/tool 指标。

## D-012：文档中文优先，代码英文

**决策：** 文档、注释和用户说明默认中文；代码标识符、路径、API 字段、模型名、框架名保留英文。

**原因：** 项目主要用于中文学习和面试表达，但工程代码需要保持通用风格。

**影响：** 所有新增 Markdown 使用中文写作，必要英文只保留技术名词。

## D-013：V2 深化范围重新打开但受 Harness 边界约束

**决策：** 为了形成 2026 年 Agent 后端简历亮点，重新打开 Loop Engineering、MCP 风格 adapter、Agent Safety Eval 和 Artifact Timeline。

**原因：** V1 已完成 Agent Harness + RAG 主链路。继续只强调 RAG 容易与大众简历重合，需要把重点上移到 Agent 执行治理、评测、工具边界和失败修复闭环。

**影响：** 新能力必须保持 fake/local first。MCP adapter 不能绕过现有 Tool Registry、approval、ACL、citation 和 trace 约束。所有新增评测必须可重复，不能依赖真实云模型作为单元测试前提。
