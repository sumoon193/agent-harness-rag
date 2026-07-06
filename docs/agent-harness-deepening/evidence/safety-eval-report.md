# Agent Safety Eval 落地证据

## 落地范围

- 新增 `app/schemas/safety.py`：安全评测 case、result、report schema。
- 新增 `app/services/evaluation/safety_eval.py`：deterministic 安全评测器。
- 新增 `POST /eval/safety`：默认运行本地 fake 安全样例，也支持传入结构化 cases。

## 风险覆盖

- 越权检索：禁止无权限文档出现在 retrieval hits。
- Prompt Injection：使用 `PromptGuard` 检测注入指令。
- 引用缺失：用户可见答案必须有 citations。
- 写工具误调用：写工具只有 approval `approved` 后才可执行。
- 成本失控：loop 次数不能超过预算。

## 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest tests\service\test_agent_safety_eval.py tests\api\test_harness_deepening_api.py::test_safety_eval_endpoint_returns_structured_report -q -p no:cacheprovider
```

当前结果：安全评测 service 与 API 均通过。
