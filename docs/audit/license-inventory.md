# DevMate 许可证与第三方来源清单

> 归属：W1-C1 审计卡输出，供 W1/W2 go/no-go 决策使用，不是法律意见。
> 基线：`12cd6805c4864a71a6fbc2afd7e281ca1262f1e2`（工作树 dirty，含本卡审计输出）
> 日期：2026-08-03
> 范围：仓库根许可证、运行时/开发依赖、模型与数据来源；逐文件复用决定见 `origin-map.jsonl`。

## 1. 仓库自有代码许可证

仓库根 `LICENSE` 为 **Apache-2.0**。该文件证明仓库自有代码的发布条款，但不能单独证明每个第三方来源文件的归属与复用条件；逐文件来源和决定由 `docs/audit/origin-map.jsonl` 与 `docs/audit/domain-coupling.md` 记录。

## 2. 运行时依赖许可证（来自 `pyproject.toml` / `uv.lock`）

以下许可证取自当前 `.venv` 内已安装发行版的 `METADATA`（`License-Expression` / `License`），不是猜测。

| 依赖 | 用途 | 许可证 | 归属决定 |
| --- | --- | --- | --- |
| fastapi | HTTP API 框架 | MIT | allowed |
| pydantic / pydantic-settings | 数据校验与配置 | MIT | allowed |
| sqlalchemy | ORM | MIT | allowed |
| langgraph | 状态机编排 | MIT | allowed |
| langgraph-checkpoint-postgres | 持久化 checkpointer | MIT | allowed |
| uvicorn | ASGI 服务器 | BSD-3-Clause | allowed |
| jinja2 | 模板渲染 | BSD License | allowed |
| asyncpg | PostgreSQL 异步驱动 | Apache-2.0 | allowed |
| redis | 缓存与 rate limit | MIT | allowed |
| minio | 对象存储 | Apache-2.0 | allowed |
| pymilvus | 向量库客户端 | Apache Software License | allowed |
| elasticsearch | BM25 检索 | Apache-2.0 | allowed |
| celery | 异步任务 | BSD-3-Clause | allowed |
| opentelemetry-sdk / exporter-otlp-http | 可观测性 | Apache-2.0 | allowed |
| pypdf | PDF 解析 | BSD-3-Clause | allowed |
| python-docx | DOCX 解析 | MIT | allowed |
| openpyxl | XLSX 解析 | MIT | allowed |
| python-pptx | PPTX 解析 | MIT | allowed |
| aiosqlite | SQLite 异步驱动 | MIT | allowed |
| python-multipart | 文件上传解析 | Apache-2.0 | allowed |
| aiohttp | 异步 HTTP | Apache-2.0 AND MIT | review（双重许可需按场景确认引用条款） |
| psycopg[binary] | PostgreSQL 驱动 | LGPL-3.0-only | review（LGPL 在商业闭源分发的约束需人工确认） |

## 3. 开发依赖许可证

| 依赖 | 用途 | 许可证 | 归属决定 |
| --- | --- | --- | --- |
| pytest | 测试框架 | MIT | allowed |
| pytest-asyncio | 异步测试 | Apache-2.0 | allowed |
| pytest-cov | 覆盖率 | MIT | allowed |
| vulture | 死代码审计（P3 工具链） | MIT | allowed |

## 4. 模型与数据来源

- **Qwen Cloud（DashScope）chat / embedding / rerank**：通过 API 调用，不随仓库重新分发模型权重或客户端代码；密钥只存在于 `.env`，仓库不记录。`docs/audit/origin-map.jsonl` 把 `.env` 标为 `unknown` + `review`，`evidence_refs` 不含正文。
- **demo 文档与坏样本**（`demo_docs/`）：项目自建演示语料，Apache-2.0 仓库自有内容。
- **面经调研数据**：存放于学习仓库 `D:\Code\agent study\调研数据\`，不在本项目仓库内，不属于本清单的复用范围。

## 5. 复用决定口径

`origin-map.jsonl` 的 `reuse_decision` 含义：

- `allowed`：来源提交 + 仓库 Apache-2.0 证据齐全，属于 Runtime Kernel，允许进入后续复用评审。
- `isolate`：来源可追溯但属于 HR/RAG 领域，必须与 Runtime Kernel 隔离。
- `review`：来源、许可证或领域证据不完整，需要人工复核（例如 `.env`、`psycopg`、`aiohttp`、未跟踪文件）。
- `blocked`：当前不能复用或发现硬性边界问题（例如领域耦合扫描确认的 Runtime 直接依赖）。

许可证未知或来源不明时只能为 `review` 或 `blocked`，绝不允许推断为 `allowed`。

## 6. 待复核项（review）

1. `psycopg`（LGPL-3.0-only）：仅作为 PostgreSQL 驱动使用，不修改、不分发其源码；商业分发约束待人工确认。
2. `aiohttp`（Apache-2.0 AND MIT）：双重许可，需按实际分发方式选择条款。
3. `.env` 及敏感路径：只识别文件名，不读取正文；复用决定固定为 `review`。
4. 当前公开说明仅保留工程实施、验证和运维资料。
5. 所有 `docs/audit/`、`scripts/audit_origin_map.py`、`scripts/scan_domain_coupling.py`、`tests/audit/` 新文件：本卡自身产出，来源提交待与审计提交一起确认。

## 7. 证据索引

- 仓库根许可证：`LICENSE`
- 依赖声明：`pyproject.toml`
- 依赖锁文件：`uv.lock`
- 逐文件来源与决定：`docs/audit/origin-map.jsonl`
- 领域耦合命中：`docs/audit/domain-coupling.md`
- 审计合同：`docs/audit/origin-map.schema.json`
