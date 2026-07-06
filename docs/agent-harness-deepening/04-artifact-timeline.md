# Artifact Timeline 设计

## 目标

把 Agent Run 中分散的 evidence、plan、approval、tool call、tool result、trace、eval 结果串成时间线，便于演示、排障和面试复盘。

## 事件类型

- `run_created`
- `evidence_retrieved`
- `plan_generated`
- `tool_call_prepared`
- `approval_requested`
- `approval_decided`
- `tool_executed`
- `reflection_created`
- `repair_action_created`
- `answer_generated`
- `eval_completed`

## 展示字段

- 时间。
- 阶段。
- 输入摘要。
- 输出摘要。
- 风险等级。
- 关联 citation。
- 关联 trace span。
- 审批状态。

## 边界

- Timeline 是复盘视图，不是新的事实来源。
- Timeline 不保存敏感原文，只保存摘要和引用 ID。
- 对外展示前必须做 PII 脱敏。

## 验收样例

- 一次成功 run 能看到完整链路。
- 一次审批拒绝 run 能看到停在哪里。
- 一次工具失败 run 能看到失败、反思和修复建议。
