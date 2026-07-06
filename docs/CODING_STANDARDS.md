# 代码实现规范

> 本文件定义 EnterpriseMind Agent Harness RAG 项目的编码标准。
> 所有代码实现必须遵循本规范。

---

## 1. 项目结构

```
app/
├── main.py                 # FastAPI 入口，只做 app 创建和路由挂载
├── config.py               # Pydantic Settings，唯一配置源
├── dependencies.py         # FastAPI 依赖注入函数
├── core/                   # 基础设施连接（数据库、Redis、Milvus、ES、MinIO）
│   ├── database.py
│   ├── redis_client.py
│   └── ...
├── models/                 # SQLAlchemy ORM 模型
│   ├── base.py             # DeclarativeBase
│   └── ...
├── schemas/                # Pydantic 请求/响应 Schema
│   └── ...
├── services/               # 业务逻辑层（核心，不允许依赖 FastAPI）
│   ├── parser/
│   ├── chunker/
│   ├── embedding/
│   ├── indexer/
│   ├── retrieval/
│   ├── agent/
│   ├── tools/
│   ├── evaluation/
│   ├── security/
│   └── observability/
├── api/                    # 路由层（只做协议适配，不承载业务逻辑）
│   └── v1/
│       ├── router.py       # 路由聚合
│       └── ...
├── middleware/              # 中间件（认证、限流、租户）
├── prompts/                # Prompt 模板（Jinja2）
└── worker/                 # Celery Worker
```

### 规则

- `services/` 不得导入 `fastapi`、`starlette` 或任何 Web 框架类型。
- `api/` 不得包含业务判断逻辑，只做参数解析、调用 service、格式化响应。
- `schemas/` 只做数据定义和校验，不包含业务方法。
- `models/` 只做 ORM 映射，不包含业务方法。
- `core/` 只做连接和客户端初始化，不包含业务逻辑。

---

## 2. 命名规范

| 类型 | 规则 | 示例 |
|------|------|------|
| 模块文件 | snake_case | `hybrid_retriever.py`、`agent_run.py` |
| 类名 | PascalCase | `HybridRetriever`、`AgentRunManager` |
| 函数/方法 | snake_case | `search()`、`create_run()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_CHUNK_SIZE`、`DEFAULT_TOP_K` |
| 私有方法 | 前缀下划线 | `_build_filter()`、`_validate_acl()` |
| Pydantic Schema | PascalCase + 后缀 | `ChatRequest`、`AnswerResponse`、`DocumentCreate` |
| SQLAlchemy Model | PascalCase，单数 | `Document`、`AgentRun`、`Chunk` |
| 枚举 | PascalCase 类名 + UPPER 值 | `RunStatus.COMPLETED` |
| 测试文件 | `test_` 前缀 | `test_hybrid_retrieval.py` |
| 测试函数 | `test_` 前缀 + 描述 | `test_search_returns_relevant_chunks()` |

---

## 3. 类型注解

- **所有函数签名必须有完整类型注解**，包括参数和返回值。
- 使用 `from __future__ import annotations` 启用延迟求值。
- 复杂类型使用 `TypeAlias` 提高可读性。

```python
from __future__ import annotations
from typing import TypeAlias

ChunkId: TypeAlias = str
Score: TypeAlias = float

async def search(
    query: str,
    top_k: int = 10,
    acl_filter: dict | None = None,
) -> list[RetrievalResult]:
    ...
```

- 不使用 `Any`，除非确实无法确定类型（需注释说明原因）。
- Optional 使用 `X | None` 语法，不用 `Optional[X]`。
- 集合类型使用内置泛型：`list[str]`、`dict[str, int]`，不用 `List`、`Dict`。

---

## 4. 错误处理

### 自定义异常层次

```python
# app/core/exceptions.py
class AppError(Exception):
    """应用层基础异常"""
    pass

class NotFoundError(AppError):
    """资源不存在"""
    pass

class PermissionError(AppError):
    """权限不足"""
    pass

class ValidationError(AppError):
    """业务校验失败"""
    pass

class ExternalServiceError(AppError):
    """外部服务调用失败"""
    pass
```

### 规则

- Service 层抛出自定义异常，不抛出 `ValueError`、`RuntimeError` 等通用异常。
- API 层捕获自定义异常，映射为 HTTP 状态码。
- 外部服务调用（Milvus、ES、LLM API）必须捕获底层异常并包装为 `ExternalServiceError`。
- Celery task 必须捕获所有异常并更新任务状态为 FAILED，记录 error_message。
- 不使用 bare `except:` 或 `except Exception:` 后静默吞掉错误。

```python
# API 层示例
@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile):
    try:
        doc = await document_service.upload(file)
        return DocumentResponse.model_validate(doc)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

---

## 5. 依赖注入

### FastAPI 依赖

```python
# app/dependencies.py
from functools import lru_cache
from app.config import Settings
from app.core.database import AsyncSession

@lru_cache
def get_settings() -> Settings:
    return Settings()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

### Service 层依赖

- Service 通过构造函数接收依赖（数据库 session、外部客户端等），不直接导入全局单例。
- 每个 Service 定义 Protocol 或 ABC 作为接口，便于测试时替换为 fake。

```python
# app/services/retrieval/base.py
from typing import Protocol

class Retriever(Protocol):
    async def search(self, query: str, top_k: int, acl_filter: dict | None) -> list[RetrievalResult]: ...

# app/services/retrieval/hybrid_retriever.py
class HybridRetriever:
    def __init__(self, dense: Retriever, sparse: Retriever, reranker: Reranker):
        self._dense = dense
        self._sparse = sparse
        self._reranker = reranker
```

---

## 6. Adapter / Fake 模式

所有外部依赖必须有 adapter 接口和 in-memory fake 实现：

```
app/services/embedding/
├── base.py             # Embedder Protocol
├── qwen_cloud.py       # 真实 Qwen Cloud 实现
└── fake.py             # 确定性 fake 实现（用于测试和本地开发）
```

### Fake 实现规则

- Fake 必须是**确定性**的：相同输入产生相同输出。
- Fake 不依赖网络、磁盘或外部服务。
- Fake 用于：单元测试、本地开发、CI。
- 真实 adapter 用于：集成测试（标记 `@pytest.mark.integration`）、生产环境。

```python
# app/services/embedding/fake.py
class FakeEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """确定性 fake：对文本 hash 生成固定向量"""
        return [self._hash_to_vector(t) for t in texts]

    def _hash_to_vector(self, text: str) -> list[float]:
        import hashlib
        h = hashlib.md5(text.encode()).hexdigest()
        return [int(h[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
```

---

## 7. 日志规范

### 使用标准库 logging

```python
import logging

logger = logging.getLogger(__name__)
```

### 日志级别

| 级别 | 用途 |
|------|------|
| DEBUG | 开发调试信息（chunk 内容、embedding 维度、filter 表达式） |
| INFO | 关键业务事件（文档入库开始/完成、Agent Run 状态变更、工具调用） |
| WARNING | 可恢复的异常（重试、降级、fallback） |
| ERROR | 不可恢复的错误（外部服务失败、任务失败） |
| CRITICAL | 系统级故障（数据库连接断开、配置缺失） |

### 结构化日志

```python
logger.info(
    "document_ingested",
    extra={
        "document_id": doc_id,
        "chunk_count": len(chunks),
        "parser": "docling",
        "duration_ms": elapsed,
    },
)
```

### 禁止

- 不在日志中打印 API key、密码、token。
- 不在循环中打印 INFO 级别日志（用 DEBUG）。
- 不用 `print()` 替代 logging。

---

## 8. 测试规范

### 目录结构

```
tests/
├── conftest.py                 # 全局 fixtures
├── test_health.py
├── test_documents.py
├── test_ingestion.py
├── test_parsers.py
├── test_chunkers.py
├── test_contextual.py
├── test_indexing.py
├── test_hybrid_retrieval.py
├── test_agent_run.py
├── test_tool_registry.py
├── test_agent_graph.py
├── test_e2e_agent.py
├── test_evaluation.py
├── test_acl.py
├── test_security.py
├── fixtures/                   # 测试数据文件
│   ├── sample.pdf
│   ├── sample.docx
│   └── ...
└── eval/
    └── golden_dataset.jsonl
```

### 命名规则

- 测试文件：`test_<module_name>.py`
- 测试函数：`test_<what>_<condition>_<expected_result>()`
- 示例：`test_search_with_acl_filter_excludes_unauthorized_docs()`

### Fixtures

```python
# tests/conftest.py
import pytest
from app.services.embedding.fake import FakeEmbedder
from app.services.retrieval.hybrid_retriever import HybridRetriever

@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()

@pytest.fixture
def sample_chunks() -> list[dict]:
    return [
        {"id": "1", "text": "新员工入职需提交身份证复印件", "page": 1},
        {"id": "2", "text": "试用期为三个月", "page": 2},
    ]
```

### 测试分层

| 层 | 标记 | 依赖 | 示例 |
|----|------|------|------|
| 单元测试 | 无标记 | 只用 fake/mock | `test_chunker_splits_by_heading()` |
| 集成测试 | `@pytest.mark.integration` | 真实外部服务 | `test_milvus_insert_and_search()` |
| E2E 测试 | `@pytest.mark.e2e` | 完整系统 | `test_full_agent_run_with_approval()` |

### 运行命令

```bash
pytest                                    # 只跑单元测试
pytest -m integration                     # 跑集成测试
pytest -m e2e                             # 跑 E2E 测试
pytest --cov=app --cov-report=term-missing # 覆盖率报告
```

### 覆盖率要求

- 核心 service 层（retrieval、agent、chunker、evaluation）：≥ 80%
- API 层：≥ 70%
- 工具和辅助模块：≥ 60%

---

## 9. Pydantic Schema 规范

### 命名后缀

| 后缀 | 用途 | 示例 |
|------|------|------|
| `Request` | API 请求体 | `ChatRequest`、`UploadRequest` |
| `Response` | API 响应体 | `AnswerResponse`、`DocumentResponse` |
| `Create` | 创建操作输入 | `DocumentCreate` |
| `Update` | 更新操作输入 | `DocumentUpdate` |
| 无后缀 | 内部数据传输 | `Chunk`、`RetrievalResult`、`Citation` |

### 规则

- Schema 使用 `model_validate()` 从 ORM 对象转换，不在 Schema 中写 `from_orm` 方法。
- 响应 Schema 使用 `model_config = ConfigDict(from_attributes=True)`。
- 字段使用 `Field(description=...)` 提供文档说明。
- 枚举字段使用 `StrEnum` 或 `str, Enum`。

---

## 10. 异步规范

- 所有 I/O 操作（数据库、网络、文件）使用 `async/await`。
- CPU 密集操作使用 `asyncio.to_thread()` 避免阻塞事件循环。
- 不在 async 函数中调用同步阻塞代码（如 `time.sleep()`，用 `asyncio.sleep()`）。
- Celery task 是同步的（Celery worker 不运行在 asyncio 事件循环中），内部需要异步调用时使用 `asyncio.run()`。

---

## 11. 导入规范

```python
# 1. 标准库
import hashlib
import logging
from datetime import datetime
from typing import TypeAlias
from uuid import UUID, uuid4

# 2. 第三方库
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

# 3. 本项目
from app.config import Settings
from app.models.document import Document
from app.schemas.chat import ChatRequest, AnswerResponse
from app.services.retrieval.hybrid_retriever import HybridRetriever
```

### 规则

- 不使用 `from module import *`。
- 相对导入用于同 package 内：`from .base import Retriever`。
- 跨 package 使用绝对导入：`from app.services.retrieval.base import Retriever`。
- 每个 import 组之间空一行。

---

## 12. Prompt 模板规范

- 所有 Prompt 使用 Jinja2 模板，存放在 `app/prompts/` 目录。
- 不在业务代码中硬编码 Prompt 字符串。
- Prompt 模板有版本号或名称标识，便于 A/B 实验。
- 变量用 `{{ variable }}`，控制流用 `{% %}`。

```python
# app/prompts/templates.py
from jinja2 import Environment, BaseLoader

_env = Environment(loader=BaseLoader())

ANSWER_PROMPT = _env.from_string("""
你是一个企业知识库问答助手。请仅根据以下证据回答。

## 证据
{% for ev in evidence %}
[{{ loop.index }}] {{ ev.source }} 第{{ ev.page }}页: {{ ev.text }}
{% endfor %}

## 问题
{{ question }}

## 约束
1. 仅使用证据回答
2. 用 [1][2] 标注引用
3. 证据不足则拒答
""")
```

---

## 13. 配置规范

- 所有配置通过 `app/config.py` 的 Pydantic Settings 读取环境变量。
- 敏感配置（API key、密码）只在 `.env` 中，不进代码仓库。
- `.env.example` 包含所有变量名和说明，不含真实值。
- 配置项有合理默认值，开发环境可以不配 `.env` 也能启动（使用 fake）。

---

## 14. 代码审查清单

每次实现后自查：

- [ ] 函数有完整类型注解
- [ ] 错误使用自定义异常，不静默吞错
- [ ] 外部依赖通过 Protocol/ABC 注入，有 fake 实现
- [ ] 日志使用 logging，不用 print
- [ ] 测试覆盖关键路径和失败路径
- [ ] 无硬编码 API key 或密码
- [ ] 业务逻辑不在 API 层
- [ ] 导入顺序正确
- [ ] Prompt 使用模板，不硬编码
