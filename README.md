# EnterpriseMind Agent Harness RAG

EnterpriseMind Agent Harness RAG 是一个面向企业 HR 知识任务的智能体平台。它不是普通的 RAG Chatbot，而是把 **RAG 可信证据层** 和 **Agent Harness 执行治理层** 组合起来，让企业知识问答、任务规划、工具审批和运行审计形成一个可控闭环。

## 项目解决什么问题

企业内部制度、合同、操作手册、会议纪要和产品文档通常分散在不同系统里，存在几个典型问题：

- 文档格式复杂，解析和入库成本高。
- 单纯关键词或向量检索不稳定，条款编号和语义问题难以兼顾。
- LLM 回答容易缺乏引用来源，难以判断是否幻觉。
- Agent 一旦能调用工具，就可能产生不可控副作用。
- 企业场景需要权限隔离、审批、审计、trace 和评测。

本项目的答案是：RAG 提供可追溯证据，Agent Harness 负责治理 agent 如何使用这些证据和工具。

## 核心亮点

- **Agent Run 生命周期**：完整记录意图识别、检索、计划、工具调用、审批、恢复执行和最终回答。
- **Human-in-the-Loop 审批**：写入型工具如 `create_mock_hr_ticket` 必须等待用户审批。
- **RAG 证据层**：所有回答都基于 evidence 和 citations，证据不足时拒答或追问。
- **混合检索**：Dense vector、Sparse / BM25、RRF、reranker 组合处理语义查询和精确条款查询。
- **多格式文档入库**：Docling / MinerU 解析企业文档，保留章节、页码、表格和引用映射。
- **ACL 权限隔离**：检索前过滤，生成前二次校验，避免越权 evidence 进入上下文。
- **评测与可观测**：RAGAS 指标 + Phoenix / OpenTelemetry trace，支持 A/B 对照和链路排查。
- **V2 扩展**：GraphRAG / LightRAG 与 MCP 作为增强方向，不阻塞 V1。

## 标准 Demo

用户输入：

> 新员工入职到转正要办哪些事项？

系统流程：

1. 创建 `AgentRun`。
2. 检索 HR 制度文档 evidence。
3. 生成办理计划和 checklist。
4. 准备调用 `create_mock_hr_ticket`。
5. Harness 暂停并展示审批卡片。
6. 用户 Approve / Edit / Reject。
7. 审批通过后从 checkpoint 恢复，返回 mock ticket result、citations 和 trace。

## 技术栈

- 当前已实现：Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.0、LangGraph、Jinja2、aiohttp、Celery、pytest、pytest-asyncio、pytest-cov、Vue 3、Element Plus、Pinia、Playwright。
- 当前运行模式：fallback mode 使用 pure Python / in-memory / deterministic fake；full mode 已接入 PostgreSQL、Redis、Milvus、Elasticsearch、MinIO、Qwen 真实 chat / embedding / rerank adapter，以及可选 Celery 文档入库链路。
- 规划后续接入：Docling / MinerU、RAGAS、Phoenix / OpenTelemetry、Docker Compose 深化。

## 文档导航

- `AGENTS.md`：通用 agent 入口记忆。
- `CLAUDE.md`：Claude 类 agent 入口记忆。
- `项目亮点.md`：项目亮点、面试话术和参考资料。
- `开发规划.md`：16 阶段完整开发规划。
- `docs/CODING_STANDARDS.md`：代码实现规范。
- `docs/modules/00-模块规范总览.md`：模块规范总入口。
- `docs/modules/*.md`：每个模块的详细开发规范。
- `docs/DECISIONS.md`：关键产品和技术决策。
- `RAG项目面试亮点.md`：早期参考材料，仅作追溯。

## 推荐开发顺序

1. 先实现后端纯领域闭环，不依赖 Docker 和云 API。
2. 再暴露 FastAPI 接口，打通 Agent Run、审批、评测。
3. 再接 PostgreSQL、Redis、Milvus、Elasticsearch、MinIO、Celery。
4. 再做前端控制台，展示 evidence、approval、trace、eval。
5. 最后做 GraphRAG / MCP / Phoenix 深度增强。

## 面试可讲版本

这个项目不是普通 RAG 问答，而是 Agent Harness + RAG 的企业知识任务平台。RAG 负责提供制度证据，Agent Harness 负责控制 agent 的执行过程，包括任务规划、工具调用、审批中断、状态恢复、ACL 过滤、trace 和评测。比如用户问“新员工入职到转正要办哪些事项”，系统会先检索 HR 制度证据，再生成办理清单；如果要创建 HR 工单，Harness 会暂停并等待用户审批，通过后才执行模拟工具。这样既能回答问题，也能体现企业级 agent 的安全、可控和可追踪。

## 当前状态（2026-06-01）

后端 pure Python / in-memory / deterministic fake 主链路已经完成，并补齐 FastAPI fallback API、Vue 3 + Element Plus 前端控制台与 Playwright E2E 验收闭环：

- 数据模型与 Schema：ORM / Pydantic schema / 审批与工具状态枚举。
- 文档上传与入库：Storage Protocol / LocalFileStorage / IngestionPipeline 七阶段状态。
- 文档解析与分块：Markdown、Plain Text、Structural / Semantic / Hybrid chunking。
- in-memory 检索：mock embedding、vector store、BM25、RRF、mock reranker、EvidenceBundle。
- Agent Harness：Agent Run、工具注册与执行、写入型工具审批、resume、tool_calls 历史记录。
- LangGraph 工作流：MemorySaver、dynamic interrupt/resume、SSE 事件。
- Grounded Answer 与评测：Jinja2 prompt、citation、低置信度处理、fact check、fake RAGAS。
- ACL、安全与可观测：权限过滤、Prompt Injection、PII 脱敏、rate limit、audit log、fallback trace。
- FastAPI API：health、documents、ingestions、agent-runs、approvals、eval runs、统一错误格式和 RequestID。
- 前端控制台：文档入库状态、Agent Run、evidence、plan/steps、approval card、tool result、trace、eval 页面。
- 测试质量门禁：unit / service / api 分层、pytest markers、quality gate 脚本。
- 2026-06-01 审查补强：Milvus 检索 ACL 下推到查询表达式、入库重试清理旧向量索引、Approve 决策写入审计步骤、Elasticsearch 宿主端口统一为 9201。
- 2026-06-01 full-mode 补强：PostgreSQL 快照持久化先 upsert tool_calls 再 upsert approvals，并保存 approval decision / decided_by / decided_at，修复 full 模式审批恢复时的外键失败。
- 2026-06-01 真实 AI 链路：Qwen chat completion、text-embedding-v4 embedding、qwen3-rerank reranker adapter；有 `QWEN_API_KEY` 时 full mode 启用真实 AI，缺 key 时保持 fake。
- 2026-06-01 Celery 入库链路：Celery app、文档入库 dispatcher、worker job、Redis/In-memory ingestion task store、storage-backed payload；默认 `sync`，开启 `INGESTION_EXECUTION_MODE=celery` 后上传返回 queued。
- 2026-06-01 真实 embedding 批处理：`EMBEDDING_BATCH_SIZE=10`，避免 Qwen embedding 单批超过 10 条。
- 2026-06-01 最终构建补强：新增 `AGENT_RUN_ENGINE=langgraph` 可选真实 LangGraph API 编排、Phoenix / OpenTelemetry OTLP trace、MilvusClient adapter、Redis `aclose()` 与前端动态 health 状态。

当前 V1 主链路已完整接入：fallback demo、可选 LangGraph API 编排、Qwen chat/embedding/rerank、Celery 入库、PostgreSQL / Redis / Milvus / Elasticsearch / MinIO adapter、Phoenix / OTel trace 与前端控制台。GraphRAG / LightRAG、MCP、真实 HR 系统、完整生产多租户 RBAC 仍作为 V2 非目标保留。

常用验证命令：

```bash
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests\integration -m integration -q -p no:cacheprovider
.\.venv\Scripts\python.exe scripts\quality_gate.py
.\.venv\Scripts\python.exe scripts\v1_final_check.py
.\.venv\Scripts\python.exe -m compileall -q app tests scripts
.\.venv\Scripts\python.exe scripts\smoke_qwen_ai.py
.\.venv\Scripts\celery.exe -A app.services.ingestion.celery_app.celery_app worker --loglevel=info --pool=solo
cd frontend && npm run build
cd frontend && npm run test:e2e
cd frontend && $env:APP_MODE='full'; npm run test:e2e  # 需要外部中间件已启动
```

最新验收记录（2026-06-01）：

- 后端基线：`197 passed`，`11 deselected`，仅 FastAPI TestClient deprecation warning。
- 质量门禁：全部通过（内部基线 `197 passed`，`11 deselected`）。
- V1 收尾脚本：通过；full-mode 外部服务端口当前标记为 blocked，默认不阻塞 V1 closure。
- integration：本轮因 PostgreSQL / Redis / Milvus / Elasticsearch / MinIO 本地端口均未启动而阻塞；Docker CLI 当前不可用。上一轮这些 adapter 已通过 full mode 验证。
- Qwen 冒烟：本轮沙箱网络被拒且外部网络审批因额度限制未获准；上一轮 chat / embedding / rerank 均为 ok，embedding dimension=1024。
- Celery eager smoke：`run_ingestion_task.delay(...).get()` 返回 `ready 1.0 2`。
- demo 文档：`demo_docs/hr_onboarding_regularization_policy_2026.md` 已通过 full-mode API 入库，返回 `doc_b9cd0f168cc3` / `ing_4424c0b17fba`，状态 `ready`，20 个分块。
- 前端构建：通过；仅第三方 `@vueuse/core` pure annotation 与 chunk size warning。
- Playwright E2E fallback：`5 passed`，覆盖文档入库、Agent Run/SSE、Approve/Edit/Reject、citations、trace。
- full mode `/health`：上一轮为 200 且 PostgreSQL / Redis / Milvus / Elasticsearch / MinIO 均为 up；本轮当前机器这些端口均拒绝连接，需先启动外部服务。

## V1 收尾

本仓库当前按 V1 closure 收尾，V2 不继续扩展。V1 边界包括 fallback demo、FastAPI API、前端控制台、Agent Harness 审批恢复、RAG evidence/citations、真实 Qwen adapter、Celery 入库、full-mode 基础设施 adapter、可选 LangGraph API 编排和 Phoenix/OTel trace。

V2 冻结项包括 GraphRAG / LightRAG、MCP Server、真实 HR 系统和完整生产多租户 RBAC。

新增 V1 收尾检查脚本：

```powershell
.\.venv\Scripts\python.exe scripts\v1_final_check.py
```

默认脚本会列出 V1 代码验收命令，并探测 PostgreSQL、Redis、MinIO、Elasticsearch、Milvus 本地端口。外部服务未启动时会标记为 blocked，但不让 V1 closure 失败。需要把 full-mode 外部服务作为硬验收时运行：

```powershell
.\.venv\Scripts\python.exe scripts\v1_final_check.py --require-full
```
