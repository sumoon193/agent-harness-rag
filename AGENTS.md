# EnterpriseMind Agent Harness RAG - 通用 Agent 入口

这份文档是给 Codex、Claude、Cursor、Copilot 等通用 agent 的项目入口记忆。进入本项目后，先读本文件，再按文档索引读取对应规范。

## 项目定位

EnterpriseMind Agent Harness RAG 不是普通 RAG Chatbot。

核心架构是：

- **RAG 作为可信证据层**：负责文档入库、解析、分块、索引、检索、重排、引用和评测。
- **Agent Harness 作为智能体执行治理层**：负责 Agent Run 生命周期、计划生成、工具注册、人工审批、checkpoint/resume、权限控制、审计日志和 trace。

V1 场景聚焦 HR 制度流程问答与任务执行，例如入职、转正、报销、请假和 HR 工单。

## 必读文档顺序

开发前按顺序阅读：

1. `CLAUDE.md`：当前项目状态、关键约束和快速索引。
2. `项目亮点.md`：项目亮点、技术叙事和面试表达。
3. `开发规划.md`：完整 16 阶段规划和推荐实施顺序。
4. `docs/modules/00-模块规范总览.md`：模块规范入口。
5. `docs/CODING_STANDARDS.md`：代码实现规范。
6. 当前任务对应的 `docs/modules/*.md`。
7. `docs/DECISIONS.md`：关键产品和技术决策。

`RAG项目面试亮点.md` 是早期参考材料，已被 `项目亮点.md` 综合吸收，除非需要追溯原始想法，否则不作为当前主规范。

## 推荐开发顺序

实际开发不要一开始就全量上 Docker 和外部中间件。推荐顺序：

1. 纯后端领域闭环：schemas、chunking、in-memory retrieval、Agent Harness、审批恢复、deterministic eval。
2. API 闭环：FastAPI 暴露上传、Agent Run、审批、评测接口，先接 fallback。
3. 基础设施替换：PostgreSQL、Redis、Milvus、Elasticsearch、MinIO、Celery。
4. 前端演示台：展示 evidence、plan、approval、tool result、trace、eval。
5. V2 增强：GraphRAG / LightRAG、MCP、Phoenix 深度实验。

## 硬性约束

- 文档和注释默认中文，代码标识符使用英文。
- 先实现 pure Python / in-memory / deterministic fake，再接真实外部依赖。
- 单元测试不能依赖 Docker、云 API key 或外部网络。
- 所有外部系统必须有 adapter 和 fake。
- 写入型工具必须审批，审批前绝不能执行。
- ACL 必须在检索前生效，答案生成前二次校验 citations。
- 用户可见答案必须有 citations，证据不足时拒答或追问。
- API 层只做协议适配和服务编排，不写领域决策。
- 不把 API key、数据库密码、模型密钥写入仓库。

## V1 非目标

- 不接真实 HR 系统。
- 不实现完整生产多租户 RBAC。
- 不把 GraphRAG / LightRAG 放进 V1 主链路。
- 不实现完整 MCP Server。
- 不强制 OCR、PPT、Excel 全格式生产级解析。
- 不让 Agent 自动执行有副作用的工具。

## 标准 Demo

用户问题：

> 新员工入职到转正要办哪些事项？

期望流程：

1. 创建 Agent Run。
2. 检索 HR 制度 evidence。
3. 生成办理 plan 和 checklist。
4. 准备调用 `create_mock_hr_ticket`。
5. 因为该工具是写入型工具，Harness 暂停等待审批。
6. 用户 Approve。
7. Harness 从 checkpoint 恢复，返回 mock ticket result、citations 和 trace。

## 当前状态（2026-06-01）

代码已经完成后端 pure Python / in-memory / deterministic fake 主链路，并补齐 FastAPI fallback API、Vue 3 + Element Plus 前端控制台与 Playwright E2E 验收闭环，不再是“尚未开始”或“只有领域层”的状态。

已落地并有单元测试覆盖：

- 模块 02：数据模型与 Pydantic Schema，SQLAlchemy ORM 可导入并可在 SQLite 内存库建表。
- 模块 03：Markdown / Plain Text 上传与同步入库 fallback，Storage Protocol、本地存储、IngestionPipeline 阶段状态。
- 模块 04：Markdown / Plain Text 解析、结构化 block、Structural / Semantic / Hybrid chunking。
- 模块 05：in-memory vector store、BM25、RRF、mock embedding、mock reranker、EvidenceBundle。
- 模块 06：Agent Run 生命周期、工具注册、写入型工具审批、approval resume、tool_calls 历史记录。
- 模块 07：LangGraph in-memory workflow、dynamic interrupt/resume、SSE 事件输出。
- 模块 08：Grounded Answer、Jinja2 prompt、citation、低置信度处理、fake RAGAS 评测。
- 模块 09：ACL / 权限过滤、Prompt Injection 检测、PII 脱敏、rate limit、安全审计。
- 模块 10：fallback observability trace、span、log exporter。
- 模块 11：前端控制台，展示文档入库状态、Agent Run、evidence、plan/steps、approval card、tool result、trace、eval，并接入 fallback API / SSE。
- 模块 13：FastAPI fallback API、统一错误格式、RequestID 中间件、agent-runs / approvals / documents / ingestions / eval / health 端点。
- 模块 14：unit / service / api 测试分层、pytest markers、quality gate 脚本。
- 2026-06-01 审查补强：Milvus 检索 ACL 下推到查询表达式、IngestionPipeline 重试前清理旧向量索引、Approve 决策写入审计步骤、Elasticsearch 宿主端口统一为 9201。
- 2026-06-01 full-mode 补强：PostgreSQL 快照持久化先 upsert tool_calls 再 upsert approvals，并保存 approval decision / decided_by / decided_at，修复 full 模式审批恢复时的外键失败。
- 2026-06-01 真实 AI 链路：接入 Qwen chat completion、text-embedding-v4 embedding、qwen3-rerank reranker adapter；有 API key 时 full mode 文档入库和 Grounded Answer 使用真实 AI，缺 key 时自动保持 deterministic fake。
- 2026-06-01 Celery 入库链路：接入 Celery app、文档入库 dispatcher、worker job、Redis/In-memory ingestion task store、storage-backed payload；默认 `sync` 保持测试和 demo 稳定，设置 `INGESTION_EXECUTION_MODE=celery` 后上传返回 queued 并由 worker 异步入库。
- 2026-06-01 真实 embedding 批处理补强：IngestionPipeline 按 `EMBEDDING_BATCH_SIZE=10` 分批调用 embedding，适配 Qwen `text-embedding-v4` 单次最多 10 条输入的限制。
- 2026-06-01 最终构建补强：新增 `AGENT_RUN_ENGINE=langgraph`，API 可切到真实 LangGraph 编排并使用同一 thread 审批恢复；默认 `demo` 继续保障前端演示稳定。
- 2026-06-01 Phoenix / OTel trace：接入 `opentelemetry-sdk` 与 OTLP HTTP exporter，full mode 使用 `PHOENIX_ENDPOINT` 导出 Graph 节点级 span，fallback 继续使用 log exporter。
- 2026-06-01 适配器优化：Milvus adapter 迁移到 `MilvusClient`，Redis rate limiter 关闭连接改用 `aclose()`，前端环境状态改为读取 `/health` 动态展示。

当前已接入并在本地 full mode 验证：

- PostgreSQL / Redis / Milvus / Elasticsearch / MinIO adapter。
- Qwen chat / embedding / rerank adapter，`scripts/smoke_qwen_ai.py` 已打通真实 API。
- Celery 文档入库 task，eager smoke 已验证；独立 worker 可使用 Redis broker/result backend。
- 可选 LangGraph API 编排链路：`AGENT_RUN_ENGINE=langgraph` 时创建 run、触发 approval interrupt、同 thread resume。
- Phoenix / OpenTelemetry trace exporter：full mode 使用 OTLP HTTP 导出到 `PHOENIX_ENDPOINT`。
- `/health` full mode 可探测五个外部服务状态。

V1 已完成；仍作为 V2 非目标保留：

- GraphRAG / LightRAG、MCP、真实 HR 系统、完整生产多租户 RBAC、生产级 OCR/PPT/Excel 全格式解析。

当前验证基线：

- `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
- `.\.venv\Scripts\python.exe -m pytest tests\integration -m integration -q -p no:cacheprovider`
- `.\.venv\Scripts\python.exe scripts\quality_gate.py`
- `.\.venv\Scripts\python.exe scripts\v1_final_check.py`
- `.\.venv\Scripts\python.exe -m compileall -q app tests scripts`
- `.\.venv\Scripts\python.exe scripts\smoke_qwen_ai.py`
- `.\.venv\Scripts\celery.exe -A app.services.ingestion.celery_app.celery_app worker --loglevel=info --pool=solo`
- `cd frontend && npm run build`
- `cd frontend && npm run test:e2e`
- `cd frontend && $env:APP_MODE='full'; npm run test:e2e`（需要外部中间件已启动）

最新验收记录（2026-06-01）：

- `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`：197 passed，11 deselected，1 个 FastAPI TestClient deprecation warning。
- `.\.venv\Scripts\python.exe scripts\quality_gate.py`：全部质量门禁通过（内部基线 197 passed，11 deselected）。
- `.\.venv\Scripts\python.exe scripts\v1_final_check.py`：通过；full-mode 外部服务端口当前标记为 blocked，默认不阻塞 V1 closure。
- `.\.venv\Scripts\python.exe -m compileall -q app tests scripts`：通过。
- `.\.venv\Scripts\python.exe -m pytest tests\integration -m integration -q -p no:cacheprovider`：本轮因 PostgreSQL / Redis / Milvus / Elasticsearch / MinIO 本地端口均未启动而阻塞，Docker CLI 当前不可用。
- `.\.venv\Scripts\python.exe scripts\smoke_qwen_ai.py`：本轮沙箱内网络被拒绝，外部网络审批因额度限制未获准；上一轮已验证 Qwen chat / embedding / rerank 均为 ok，embedding dimension=1024。
- Celery eager smoke：`run_ingestion_task.delay(...).get()` 返回 `ready 1.0 2`。
- 生成并上传 demo 文档：`demo_docs/hr_onboarding_regularization_policy_2026.md` 已通过 full-mode API 入库，返回 `doc_b9cd0f168cc3` / `ing_4424c0b17fba`，状态 `ready`，20 个分块。
- `cd frontend && npm run build`：通过；仅有第三方 `@vueuse/core` pure annotation 与 chunk size warning。
- `cd frontend && npm run test:e2e`：5 passed，覆盖文档入库、Agent Run/SSE、Approve/Edit/Reject、citations、trace。
- full mode `/health`：上一轮为 200 且 PostgreSQL / Redis / Milvus / Elasticsearch / MinIO 均为 up；本轮当前机器这些端口均拒绝连接，需先启动外部服务。

当前已补充 `docker-compose.yml`、`.env.example`、`app/config.py`、full/fallback health 探测、真实 AI adapter、Celery、可选 LangGraph API 编排、Phoenix / OTel trace、MilvusClient adapter 与前端控制台。当前机器 Docker CLI 不可用，且本轮 PostgreSQL、Redis、MinIO、Milvus、Elasticsearch 端口未启动；full-mode integration/E2E 需要先恢复这些外部服务。

## V1 收尾冻结说明（2026-06-01）

用户已明确要求“完成 V1 收尾，V2 不拓展”。当前收尾口径如下：

- V1 主链路以 fallback demo、FastAPI API、前端控制台、Agent Harness 审批恢复、RAG evidence/citations、真实 Qwen adapter、Celery 入库、full-mode 基础设施 adapter、LangGraph 可选编排和 Phoenix/OTel trace 为完成边界。
- GraphRAG / LightRAG / MCP Server 不再进入当前收尾任务，统一冻结为 V2 非目标。
- 新增 `scripts/v1_final_check.py` 作为 V1 closure helper：默认列出 V1 验收命令并探测 PostgreSQL、Redis、MinIO、Elasticsearch、Milvus 本地端口；外部服务未启动时标记 blocked，但默认退出码仍为 0。
- 如需把 full-mode 外部依赖作为硬验收，运行 `.\.venv\Scripts\python.exe scripts\v1_final_check.py --require-full`，任一端口不可达都会返回非零退出码。
- 当前本机 Docker CLI 不可用，且本轮 PostgreSQL / Redis / MinIO / Milvus / Elasticsearch 端口未启动；这阻塞 full-mode integration/full E2E 复验，但不阻塞 V1 fallback 代码收尾。

## 2026-07-04 V2 深化边界更新

当前简历深化目标重新打开 V2 中的一部分能力，但范围限定为 Agent Harness 工程化深化，不改变 V1 已收尾事实。

重新打开的范围：

- Loop Engineering：把 plan、act、observe、reflect、repair 固化为可审计事件。
- MCP 风格 adapter：优先做本地 fake/server adapter，统一工具发现、schema、调用、审批和审计。
- Agent Safety Eval：覆盖越权检索、prompt injection、引用缺失、写工具误调用。
- Artifact Timeline：把 evidence、plan、approval、tool result、trace 串成可复盘时间线。

仍不进入当前范围：

- 真实 HR 系统集成。
- 完整生产多租户 RBAC。
- 大规模 GraphRAG 重构。
- 依赖远程 MCP 生态才能运行的功能。
- 必须依赖 Docker 或云 key 才能通过的单元测试。
