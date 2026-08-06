# 安全评测 Badcase 数据集

这是 EnterpriseMind Agent Runtime 的故障样例数据集，用于验证安全控制启用前后的确定性差异，并为缺陷修复提供可重复执行的回归夹具。

- **before**：安全控制关闭时的结构化观测结果（无 PromptGuard、无 ACL 下推、无审批门、无 SideEffect Ledger、使用 MemorySaver 级易失状态）。
- **after**：完整 Harness 安全链路处理相同输入后的结构化观测结果。

两份观测由同一个确定性断言引擎（`app/services/evaluation/safety_eval.py` 的 `AgentSafetyEvaluator`）评测，不依赖云模型随机输出。

## 文件

| 文件 | 层级 | 消费方式 |
| --- | --- | --- |
| `safety_cases.json` | 用例级（case-level） | 每条记录拆成两个 `SafetyEvalCase`（observations_before / observations_after），交给 `AgentSafetyEvaluator.evaluate()` |
| `trajectory_cases.json` | 轨迹级（trajectory-level） | 每条记录含两组 `RunEventEnvelope` 事件序列（events_before / events_after），交给 `AgentSafetyEvaluator.evaluate_trajectory()` |

## safety_cases.json 记录结构

字段与 `app/schemas/safety.py::SafetyEvalCase` 对齐，并增加故障背景说明字段：

```jsonc
{
  "id": "bc_inj_001",                  // 用例 ID（SafetyEvalCase.id）
  "category": "prompt_injection",      // SafetyRiskCategory 枚举值（评测引擎分派用）
  "violation_type": "prompt_injection",// 故障分类标签（7 类，见下）
  "title": "……",                       // 人类可读标题
  "input_text": "……",                  // SafetyEvalCase.input_text
  "expected_behavior": "……",           // 期望治理行为
  "forbidden_behavior": "……",          // 禁止行为
  "known_gap": false,                  // true = 当前实现已知无法拦截（诚实呈现，不计入 after 头条指标）
  "narrative": "……",                   // 故障背景、触发条件与影响说明
  "observations_before": { ... },      // 关闭治理时的结构化观测（SafetyEvalCase.observations）
  "observations_after": { ... }        // 完整 Harness 时的结构化观测
}
```

`violation_type` 七类分类学：`prompt_injection`（提示注入）、`unauthorized_retrieval`（越权检索）、`ungrounded_answer`（无证据回答）、`duplicate_write`（重复写操作）、`approval_bypass`（审批绕过尝试）、`cost_runaway`（成本失控）、`crash_recovery`（进程崩溃恢复）。前六类中，`approval_bypass` 复用引擎的 `write_tool_misuse` 分派；后两类主要在轨迹级数据集覆盖。

## trajectory_cases.json 记录结构

```jsonc
{
  "id": "bc_traj_dup_001",
  "violation_type": "duplicate_write",
  "title": "……",
  "narrative": "……",
  "expected_violations_before": ["duplicate_side_effect"],  // before 轨迹上应被检出的违规 code
  "expected_violations_after": [],                          // after 轨迹应为空
  "events_before": [ /* RunEventEnvelope 字典数组 */ ],
  "events_after":  [ /* RunEventEnvelope 字典数组 */ ]
}
```

事件字段与 `app/schemas/runtime.py::RunEventEnvelope` 完全对齐（`event_hash` 在夹具中使用 `sha256:stub` 占位；真实回放夹具应从 event store 导出并保留 hash chain）。

`evaluate_trajectory` 当前可检出的违规 code：`unauthorized_retrieval`、`write_without_approved_subject`、`duplicate_side_effect`、`answer_without_citations`。

## 运行

```powershell
.\.venv\Scripts\python.exe scripts\run_landing_eval.py --output docs\evidence\landing-eval-report.md
```

## 追加新 badcase 的约定

1. 生产或测试环境出现失败后，使用 `GET /cases/{id}/events` 导出真实事件序列。
2. 完成脱敏后写入 `trajectory_cases.json`，保留 sequence 与 event_type 的因果顺序。
3. `expected_violations_before` 记录实际发生的违规 code；修复后的轨迹写入 `events_after`。
4. 运行 `scripts/run_landing_eval.py`，确认新 case 被安全控制拦截，形成“故障记录 → 修复验证 → 回归夹具”的工程闭环。
