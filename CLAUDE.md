# EnterpriseMind Agent Harness RAG

## 项目定位

不是普通 RAG Chatbot。核心架构：**RAG 作为可信证据层 + Agent Harness 作为智能体执行治理层**。

## 技术栈

规划技术栈：Python 3.12 / FastAPI / LangGraph / LangChain Core / Celery / Redis / PostgreSQL / Milvus / Elasticsearch / Docling / Qwen Cloud / RAGAS / Phoenix / OpenTelemetry / Vue 3 / Element Plus / Docker Compose。

当前已接入依赖：Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.0、LangGraph、Jinja2、aiohttp、Celery、pytest、pytest-asyncio、pytest-cov、Vue 3、Element Plus、Pinia、Playwright。fallback mode 仍保持 pure Python / in-memory / deterministic fake；full mode 已接入 PostgreSQL、Redis、Milvus、Elasticsearch、MinIO、Qwen 真实 chat / embedding / rerank adapter，以及可选 Celery 文档入库链路。

## 关键约束

- V1 场景：HR 制度流程问答（入职、转正、报销、请假）
- V1 非目标：GraphRAG、真实 HR 系统、OCR/PPT/Excel、多租户生产 RBAC、MCP
- 开发策略：纯领域闭环优先 → API 闭环 → 基础设施替换 → 前端 → V2 增强
- 每个模块先用 in-memory/fake 实现，通过测试后再接入真实外部服务
- 用户是 Python 新手，需要逐步引导

## 文档索引

- 项目亮点：`项目亮点.md`
- 开发规划：`开发规划.md`（16 阶段 + 规划优化说明）
- 模块规范：`docs/modules/00~14`（开发前先读对应模块规范和总览）
- 原始参考：`RAG项目面试亮点.md`（已被项目亮点.md 合并，仅作参考）

## 代码实现规范

**完整规范见 `docs/CODING_STANDARDS.md`**，关键要求：

- 所有函数必须有完整类型注解（参数 + 返回值）
- Service 层抛自定义异常（`AppError` 子类），不抛通用异常
- 外部依赖通过 Protocol/ABC 注入，每个必须有 fake 实现
- 使用标准库 logging，不用 print；不在日志中泄露密钥
- 测试命名：`test_<what>_<condition>_<expected>()`；覆盖率：核心 service ≥ 80%
- Pydantic Schema 用后缀区分：Request / Response / Create / Update
- Prompt 使用 Jinja2 模板（`app/prompts/`），不硬编码
- 所有配置通过 `app/config.py` Pydantic Settings 读取，敏感值只在 `.env`

## 开发规范

- 先实现纯 Python / in-memory / deterministic fake，再接真实外部依赖
- 每个模块必须有单元测试；外部 adapter 必须有 fake 或 mock
- 写入型操作必须支持幂等、防重复执行和审计记录
- 所有用户可见回答必须能追溯到 citations 或明确说明证据不足
- ACL 必须在检索前生效，生成答案前二次校验
- 配置通过环境变量注入，不允许硬编码 API key、数据库密码和模型密钥
- API 层只负责协议适配和服务编排，不承载领域决策
- 代码标识符用英文，文档和注释用中文

## 当前状态（2026-06-01）

项目已完成后端领域闭环、FastAPI fallback API、Vue 3 + Element Plus 前端控制台和 Playwright E2E 验收闭环。

已实现：

- 数据模型与 Schema：ORM / Pydantic schema / 枚举 / 审批安全约束。
- 文档上传与入库：Storage Protocol / LocalFileStorage / IngestionPipeline 七阶段流水线。
- 文档解析与分块：Markdown、Plain Text、Structural / Semantic / Hybrid chunking。
- in-memory 检索：mock embedding、vector store、BM25、RRF、mock reranker、EvidenceBundle。
- Agent Harness：Agent Run、Step Logger、Tool Registry、Tool Executor、Approval Manager、审批恢复。
- LangGraph 工作流：MemorySaver、dynamic interrupt/resume、SSE 事件。
- Grounded Answer 与评测：Jinja2 prompt、citation、低置信度处理、fact check、fake RAGAS、agent metrics。
- ACL 与安全：检索前过滤、citation/tool 权限校验基础、Prompt Injection、PII 脱敏、rate limit、audit log。
- 可观测性：fallback trace/span/log exporter。
- FastAPI API 层：8 个端点、统一错误格式、依赖注入、RequestID 中间件。
- 前端控制台：文档入库状态、Agent Run、evidence、plan/steps、approval card、tool result、trace、eval 页面。
- 测试与质量门禁：三层目录(unit/service/api)、markers、质量门禁脚本。
- 本轮审查补强：LocalFileStorage 拒绝路径穿越 key；Agent Run 记录 tool_calls；Agent Run 详情保留已审批记录；Milvus 检索 ACL 下推到查询表达式；IngestionPipeline 重试前清理旧向量索引；Approve 决策写入审计步骤；Elasticsearch 宿主端口统一为 9201。
- full-mode 补强：PostgreSQL 快照持久化先 upsert tool_calls 再 upsert approvals，并保存 approval decision / decided_by / decided_at，修复 full 模式审批恢复时的外键失败。
- 真实 AI 链路：Qwen chat completion、text-embedding-v4 embedding、qwen3-rerank reranker adapter；full mode 有 `QWEN_API_KEY` 时启用真实 AI，缺 key 时保持 fake。
- Celery 入库链路：Celery app、文档入库 dispatcher、worker job、Redis/In-memory ingestion task store、storage-backed payload；默认 `sync`，开启 `INGESTION_EXECUTION_MODE=celery` 后上传返回 queued。
- 真实 embedding 批处理：`EMBEDDING_BATCH_SIZE=10`，避免 Qwen embedding 单批超过 10 条。
- 最终构建补强：`AGENT_RUN_ENGINE=langgraph` 可切换到真实 LangGraph API 编排并同 thread 审批恢复；默认 `demo` 保持前端演示稳定。
- Phoenix / OpenTelemetry：full mode 使用 OTLP HTTP exporter 向 `PHOENIX_ENDPOINT` 导出 Graph 节点级 span，fallback 使用 log exporter。
- 适配器优化：Milvus adapter 迁移到 `MilvusClient`；Redis rate limiter 使用 `aclose()`；前端侧栏通过 `/health` 动态展示 fallback/full 与服务状态。

已在本地 full mode 接入并验证：

- PostgreSQL / Redis / Milvus / Elasticsearch / MinIO adapter。
- Qwen chat / embedding / rerank adapter，`scripts/smoke_qwen_ai.py` 已通过真实 API 冒烟。
- Celery 文档入库 task，eager smoke 已验证；独立 worker 可使用 Redis broker/result backend。
- 可选 LangGraph API 编排链路：`AGENT_RUN_ENGINE=langgraph`。
- Phoenix / OpenTelemetry trace exporter：full mode 使用 OTLP HTTP。
- `/health` full mode 可探测五个外部服务状态。

V1 已完成；仍作为 V2 非目标保留：

- GraphRAG / LightRAG、MCP、真实 HR 系统、完整生产多租户 RBAC、生产级 OCR/PPT/Excel 全格式解析。

常用验证命令：

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

当前已补充 `docker-compose.yml`、`.env.example`、`app/config.py`、full/fallback health 探测、真实 AI adapter、Celery、可选 LangGraph API 编排、Phoenix / OTel trace、MilvusClient adapter 与前端控制台。当前机器 Docker CLI 不可用，且本轮 PostgreSQL、Redis、MinIO、Milvus、Elasticsearch 端口未启动；full-mode integration/E2E 需要先恢复这些外部服务。

## V1 收尾冻结说明（2026-06-01）

当前任务只做 V1 closure，不继续扩展 V2：

- V1 完成边界：fallback demo、FastAPI API、前端控制台、Agent Harness 审批恢复、RAG evidence/citations、真实 Qwen adapter、Celery 入库、full-mode 基础设施 adapter、LangGraph 可选编排、Phoenix/OTel trace。
- V2 冻结范围：GraphRAG / LightRAG、MCP Server、真实 HR 系统、完整生产多租户 RBAC。
- 新增 V1 收尾脚本：`.\.venv\Scripts\python.exe scripts\v1_final_check.py`。
- 默认脚本只把 full-mode 外部服务不可达标为 blocked，不让 V1 closure 失败；需要强制 full-mode 时使用 `--require-full`。
- 当前本机 PostgreSQL / Redis / MinIO / Milvus / Elasticsearch 端口未启动，Docker CLI 不可用；full-mode integration/full E2E 复验需先恢复外部服务。
