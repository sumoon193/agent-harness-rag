# Grounded Answer 与评测开发规范

本模块负责生成基于 evidence 的可信回答，并通过评测体系量化 RAG 和 Agent 表现。

## 模块职责

- Grounded answer prompt。
- Citation builder。
- Fact check。
- Low-confidence fallback。
- Golden Dataset。
- RAGAS adapter。
- Agent 自定义指标。

## AnswerResponse

```json
{
  "answer": "string",
  "citations": [],
  "confidence": 0.0,
  "refusal_reason": null,
  "tool_results": [],
  "trace_id": "trace_xxx"
}
```

## 生成约束

模型必须遵守：

1. 只使用 evidence 回答。
2. 不确定就说明证据不足。
3. 不输出用户无权限看到的信息。
4. 每个关键结论绑定 citation。
5. 工具执行结果和制度证据必须分开表达。

## 低置信规则

触发低置信：

- evidence 数量为 0。
- top rerank score 低于阈值。
- evidence 之间冲突。
- fact check 失败。
- 用户问题超出知识库范围。

处理方式：

- ask clarification。
- refusal。
- recommend human confirmation。

## Golden Dataset

字段：

- `case_id`
- `question`
- `expected_answer`
- `expected_citations`
- `expected_tools`
- `requires_approval`
- `user_context`
- `tags`

## 指标

RAG 指标：

- `context_precision`
- `context_recall`
- `faithfulness`
- `answer_relevancy`
- `answer_accuracy`

Agent 指标：

- `tool_call_accuracy`
- `approval_correctness`
- `agent_goal_completion_rate`
- `refusal_correctness`

## 不做什么

- 不让 answer service 自己重新检索。
- 不把 citations 嵌成不可解析的自然语言。
- 不用生产模型输出作为单元测试唯一断言。

## 测试要求

- `test_answer_uses_only_evidence`
- `test_answer_returns_structured_citations`
- `test_low_confidence_refuses_or_clarifies`
- `test_fact_check_rejects_unsupported_claim`
- `test_eval_runner_reports_rag_and_agent_metrics`

## 验收标准

- 标准 demo 问题返回答案、引用、confidence、tool_results。
- 无 evidence 场景不会硬答。
- 评测结果能支持 A/B 对比。

