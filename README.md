# DevMate

DevMate 是一个基于 FastAPI 和 Vue 的开发辅助服务，提供诊断、修复建议、审批和可追踪的执行流程。模型只负责生成结构化建议，权限、状态和副作用由服务端校验。

## 功能

- Webhook、诊断、修复、沙箱和审批流程
- GitHub、模型和本地执行环境的适配器
- 可恢复的运行状态、审计记录和 API 文档
- 离线测试适配器与独立的真实服务 smoke

## 技术栈

Python 3.12、FastAPI、Pydantic、SQLAlchemy、Vue、Vite。模型适配器支持 Qwen；真实 GitHub 和模型服务需要单独配置。

## Checkpoint、Event Store 与 Projection

Checkpoint 只保存执行位置，Event Store 保存业务事件，Projection 负责查询和界面展示，三者职责分开。需要跨进程恢复时可设置 `GRAPH_CHECKPOINTER_BACKEND=postgres` 并提供 `GRAPH_CHECKPOINTER_POSTGRES_URL`。

## 本地启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端开发服务器：

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

API 文档：<http://127.0.0.1:8000/docs>。健康检查：<http://127.0.0.1:8000/health>。

## 测试

```powershell
python -m pytest -q
npm --prefix frontend run build
```

## 真实服务验证

```powershell
$env:DEVMATE_BASE_URL = "http://127.0.0.1:8000"
python .\scripts\devmate\live_smoke.py --component health
python .\scripts\devmate\live_smoke.py --component model
```

模型验证需要本地设置 `QWEN_API_KEY` 和 `QWEN_CHAT_MODEL`。缺少真实配置时 smoke 会报告 `BLOCKED`，不会使用离线适配器冒充真实结果。

## 使用边界

请勿提交 `.env`、访问令牌或私有日志。离线测试中的 Fake/Recorded 适配器只用于测试，不代表外部服务已验证。

## License

MIT，见 [LICENSE](LICENSE)。
