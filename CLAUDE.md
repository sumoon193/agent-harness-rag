# DevMate 工程上下文

## 项目定位

DevMate 是 CI 失败诊断与受控修复服务，运行于 EnterpriseMind Agent Runtime。核心边界是 RAG evidence、Agent Harness 执行治理、长期 Case 状态恢复和外部副作用对账。

## 技术栈

- Python 3.12、FastAPI、Pydantic、SQLAlchemy、LangGraph、Celery。
- PostgreSQL、Redis、Milvus、Elasticsearch、MinIO。
- Qwen chat、embedding、rerank adapter。
- Phoenix、OpenTelemetry。
- Vue 3、TypeScript、Vite、Element Plus、Pinia、Playwright。

## 关键约束

- 默认离线路径不得访问外部网络；真实服务必须显式配置并独立验证。
- 所有模型输出必须经过 typed parser，不能直接推进状态或执行副作用。
- 写工具必须审批；审批绑定主体、证据、策略、命令和有效期。
- Event Store 与 Outbox 同事务；Projection 可重建；副作用使用幂等键和 `UNKNOWN` 对账。
- ACL 在检索前生效，citation 在答案生成前再次校验。
- API 层只负责协议适配和服务编排。
- 密钥只通过本机环境变量或未提交的 `.env` 注入。
- 当前体系仅保留工程实施、验证和运维资料。

## 文档索引

- 项目入口：`README.md`
- 开发规划：`开发规划.md`
- 模块规范：`docs/modules/`
- 架构：`docs/architecture/enterprise-agent-runtime-v2.md`
- 编码规范：`docs/CODING_STANDARDS.md`
- 工程决策：`docs/DECISIONS.md`
- 发布与回滚：`docs/devmate/release/release-and-rollback.md`

## 常用验证命令

```powershell
python -m pytest -q -p no:cacheprovider
python -m compileall -q app tests scripts
npm --prefix frontend run build
python scripts/devmate/live_smoke.py --component health
python scripts/devmate/live_smoke.py --component model
```

离线测试结果和 live smoke 结果必须分开记录；缺少密钥、授权或服务时保持 `blocked`，不得改写为通过。
