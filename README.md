# DevMate：企业级 Agent Runtime

## 项目简介

DevMate 是基于 EnterpriseMind Runtime 构建的工程诊断与修复协作服务。系统接收 GitHub CI 失败事件，将证据固定为可追踪 Case，并通过确定性诊断、模型辅助分析、修复计划、隔离执行、人工审批和 GitHub 副作用适配器推进完整状态链。

项目默认使用不访问外部网络的离线运行路径；真实模型和在线服务通过独立适配器与 live smoke 验证。缺少真实配置时会明确返回 `blocked`，不会把离线结果标记为真实服务通过。

## 核心能力

- 明确分离 Checkpoint、Event Store 与 Projection：Checkpoint 保存执行位置，Event Store 保存审计事实，Projection 支撑查询与界面，并与 Outbox、SideEffect Ledger 共同保障可恢复状态。
- 对重复 webhook、命令和外部副作用执行幂等校验与审计记录。
- 使用 typed command 和合法状态机推进 `created`、`running`、`waiting_approval`、`completed`、`failed`。
- 将确定性诊断与 Qwen 模型分析分离，模型输出必须通过 typed parser。
- 修复候选只在资源受限 Sandbox 中执行声明命令，写操作必须经过审批。
- 对外部调用的超时和不确定结果保留 `UNKNOWN` 状态，并通过对账恢复。
- 提供 RAG evidence、citation、ACL、Agent Run、SSE、MCP/A2A 只读协议和可观测性能力。

## 技术栈与架构

- 后端：Python 3.12、FastAPI、Pydantic、SQLAlchemy、LangGraph、Celery。
- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia。
- 数据与中间件：PostgreSQL、Redis、Milvus、Elasticsearch、MinIO。
- 模型与可观测性：Qwen、Phoenix、OpenTelemetry。
- 运行与构建：Docker Compose、pytest、Playwright、npm。

核心调用链如下：

```text
GitHub webhook
  -> evidence 固定与幂等校验
  -> DevMate Case 状态机
  -> 确定性诊断 / Qwen typed diagnosis
  -> RepairPlan 与不可变 patch
  -> Sandbox 验证
  -> Approval capability
  -> GitHub 副作用与 UNKNOWN 对账
```

详细架构见 [企业级 Agent Runtime 架构](docs/architecture/enterprise-agent-runtime-v2.md)，工程决策见 [关键决策记录](docs/DECISIONS.md)。

## 本地启动

后端默认以离线模式启动，不要求数据库、中间件或 API key：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端地址为 `http://127.0.0.1:8000`，OpenAPI 页面为 `http://127.0.0.1:8000/docs`。

另开一个 PowerShell 窗口启动前端：

```powershell
npm --prefix frontend install
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

前端地址为 `http://127.0.0.1:5173`，Vite 会把 API 请求代理到后端 `8000` 端口。

需要完整中间件时，可先运行：

```powershell
docker compose up -d
$env:APP_MODE = "full"
$env:GRAPH_CHECKPOINTER_BACKEND = "postgres"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

`.env.example` 中对应的配置写法是 `GRAPH_CHECKPOINTER_BACKEND=postgres`。checkpoint 只保存执行位置；Event Store 保存不可变审计事实，Projection 负责查询和界面读取，三者不能互相替代。

## 主要 API

| 方法与路径 | 用途 |
| --- | --- |
| `GET /health` | 返回运行模式与依赖健康状态 |
| `POST /devmate/cases` | 创建 DevMate Case |
| `POST /devmate/cases/{case_id}/commands` | 通过 typed command 推进 Case 状态 |
| `GET /devmate/cases/{case_id}/timeline` | 查询可审计状态时间线 |
| `POST /webhooks/github` | 接收 GitHub CI 失败事件并固定证据 |
| `POST /documents` | 上传并启动文档入库 |
| `GET /ingestions/{task_id}` | 查询入库任务状态 |
| `POST /agent-runs` | 创建 Agent Run |
| `GET /agent-runs/{run_id}/stream` | 订阅 Agent Run SSE |
| `POST /cases` | 创建长期 Runtime Case |
| `GET /cases/{case_id}/stream` | 订阅长期 Case SSE |
| `POST /eval/runs` | 执行评测 |
| `POST /eval/safety` | 执行安全评测 |
| `POST /mcp` | 调用本地 MCP JSON-RPC 入口 |

写接口要求服务端可信身份、稳定 request ID、权限校验和幂等语义；API 层只负责协议适配与服务编排。

## 离线测试

运行后端完整离线测试：

```powershell
python -m pytest -q -p no:cacheprovider
```

运行公开文档契约和 DevMate 定向测试：

```powershell
python -m pytest tests/governance/test_public_documentation_contract.py -q -p no:cacheprovider
python -m pytest tests/devmate tests/api/devmate -q -p no:cacheprovider
```

验证前端类型和生产构建：

```powershell
npm --prefix frontend run build
```

离线测试使用内存适配器或固定测试数据，不访问真实模型、GitHub 或其他外部服务。

## 真实服务验证

后端健康检查要求服务已经运行：

```powershell
$env:DEVMATE_BASE_URL = "http://127.0.0.1:8000"
python scripts/devmate/live_smoke.py --component health
```

Qwen 模型验证需要本机环境变量，不要把密钥写入仓库：

```powershell
$env:QWEN_API_KEY = "你的本地密钥"
$env:QWEN_CHAT_MODEL = "qwen-plus"
$env:QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
python scripts/devmate/live_smoke.py --component model
```

live smoke 的退出码合同：

- 退出码 `0`：真实服务验证通过。
- 退出码 `1`：真实服务已连接，但验证结果失败。
- 退出码 `2`：缺少配置、授权或服务不可达，状态为 `blocked`。

`health` 和 `model` 报告独立保存和判断；离线测试通过不能替代真实服务验证。

## 安全与使用边界

- 不读取或提交 `.env`、API key、Cookie、Token、私有日志和本机构建产物。
- 客户端或模型不能覆盖服务端身份、权限、审批主体和证据版本。
- 所有写副作用必须绑定审批、幂等键、审计信息和可对账状态。
- 模型只提供结构化诊断建议，不能绕过状态机、typed parser、Sandbox 或审批链。
- 单元测试默认禁用网络；真实服务只能通过显式配置和独立 live smoke 启用。
- PostgreSQL、Redis、Milvus、Elasticsearch、MinIO、GitHub 权限和远端分支保护需要分别验证，未验证项必须保持 `blocked` 或 `unverified`。

## License

本项目采用 Apache License 2.0，完整条款见 [LICENSE](LICENSE)。
