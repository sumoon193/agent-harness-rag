# DevMate 领域耦合扫描

> 归属：W1-C1 审计卡输出，供 go/no-go 决策使用；只报告耦合，不自动改写代码。
> 基线 commit：`12cd6805c4864a71a6fbc2afd7e281ca1262f1e2`
> 工作树：dirty
> 命令：`D:\Code\pythonproject\.venv\Scripts\python.exe scripts/scan_domain_coupling.py --repo . --output docs/audit/domain-coupling.md`

## 范围

路径命中 `runtime_kernel` / `runtime/` / `event_store` / `outbox` / `lease` / `timer` 的 Python 文件（与 origin-map 的 runtime_kernel 分类一致）。

## 结果

- 扫描文件：13
- 存在 HR/RAG 直接依赖（blocked）：6
- 干净（ok）：7

## go/no-go 输入

Runtime 直接引用 HR/RAG schema / prompt / API / config / reference workflow 时，对应重构入口保持 `blocked`；是否隔离由学习者复核命中清单后进入 W2 决策。

## 命中清单

| 文件 | 规则 | 类别 | 行 | 命中 |
| --- | --- | --- | ---: | --- |
| app/services/runtime/case_service.py | schema-hr-case | schema | 1 | `"""跨轮次 HRCase 应用服务。"""` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 9 | `from app.schemas.runtime import DurableTimer, ExecutionManifest, HRCase` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 28 | `self._projections: dict[str, HRCase] = {}` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 39 | `) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 44 | `aggregate_type="hr_case",` |
| app/services/runtime/case_service.py | schema-hr-policy | schema | 51 | `"policy_versions": {"hr_policy": execution_manifest.policy_version},` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 70 | `) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 75 | `aggregate_type="hr_case",` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 87 | `async def get_case(self, case_id: str) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 91 | `async def list_cases(self, *, limit: int = 100) -> list[HRCase]:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 101 | `async def rebuild(self, case_id: str) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 120 | `) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 141 | `) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 161 | `) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 181 | `) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 186 | `aggregate_type="hr_case",` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 198 | `async def _get_projection(self, case_id: str) -> HRCase:` |
| app/services/runtime/case_service.py | schema-hr-case | schema | 214 | `async def _save_projection(self, projection: HRCase) -> None:` |
| app/services/runtime/interfaces.py | schema-hr-case | schema | 9 | `HRCase,` |
| app/services/runtime/interfaces.py | schema-hr-case | schema | 52 | `async def get(self, case_id: str) -> HRCase │ None: ...` |
| app/services/runtime/interfaces.py | schema-hr-case | schema | 54 | `async def upsert(self, case: HRCase) -> None: ...` |
| app/services/runtime/interfaces.py | schema-hr-case | schema | 56 | `async def list(self, *, limit: int = 100) -> list[HRCase]: ...` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 13 | `from app.schemas.runtime import HRCase, RunEventEnvelope` |
| app/services/runtime/onboarding_workflow.py | a2a-policy-research | reference_workflow | 16 | `from app.services.a2a.policy_research import InProcessA2AClient` |
| app/services/runtime/onboarding_workflow.py | workflow-onboarding | reference_workflow | 32 | `class OnboardingCaseWorkflow:` |
| app/services/runtime/onboarding_workflow.py | a2a-policy-research | reference_workflow | 43 | `a2a_client: InProcessA2AClient,` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 73 | `) -> HRCase:` |
| app/services/runtime/onboarding_workflow.py | workflow-onboarding | reference_workflow | 87 | `skill = self._skills.resolve("hr_onboarding")` |
| app/services/runtime/onboarding_workflow.py | workflow-onboarding | reference_workflow | 89 | `raise ValidationError("Active hr_onboarding Skill is required")` |
| app/services/runtime/onboarding_workflow.py | workflow-onboarding | reference_workflow | 108 | `"onboarding_case_start",` |
| app/services/runtime/onboarding_workflow.py | workflow-onboarding | reference_workflow | 109 | `attributes={"workflow": "onboarding_to_regularization"},` |
| app/services/runtime/onboarding_workflow.py | workflow-onboarding | reference_workflow | 116 | `payload={"run_id": run_id, "workflow": "onboarding_to_regularization"},` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 241 | `) -> HRCase:` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 461 | `) -> HRCase:` |
| app/services/runtime/onboarding_workflow.py | schema-hr-policy | schema | 471 | `"hr_policy",` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 608 | `case: HRCase,` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 616 | `) -> tuple[HRCase, ApprovalRequest]:` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 719 | `case: HRCase,` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 732 | `case: HRCase,` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 738 | `) -> HRCase:` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 785 | `def _manifest_hash(case: HRCase) -> str:` |
| app/services/runtime/onboarding_workflow.py | schema-hr-case | schema | 795 | `def _manifest_hash_for_policy(case: HRCase, policy_version: str) -> str:` |
| app/services/runtime/projection.py | schema-hr-case | schema | 6 | `from app.schemas.runtime import ExecutionManifest, HRCase, RunEventEnvelope` |
| app/services/runtime/projection.py | schema-hr-case | schema | 12 | `def apply(self, current: HRCase │ None, event: RunEventEnvelope) -> HRCase:` |
| app/services/runtime/projection.py | schema-hr-case | schema | 20 | `return HRCase(` |
| app/services/runtime/projection.py | schema-hr-policy | schema | 108 | `policy_versions["hr_policy"] = str(event.payload["policy_version"])` |
| app/services/runtime/projection.py | schema-hr-case | schema | 244 | `current: HRCase,` |
| app/services/runtime/projection.py | schema-hr-case | schema | 249 | `) -> HRCase:` |
| app/services/runtime/projection.py | schema-hr-case | schema | 260 | `def rebuild(self, events: list[RunEventEnvelope]) -> HRCase:` |
| app/services/runtime/projection.py | schema-hr-case | schema | 262 | `current: HRCase │ None = None` |
| app/services/runtime/sqlalchemy_adapters.py | schema-hr-case | schema | 25 | `HRCase,` |
| app/services/runtime/sqlalchemy_adapters.py | schema-hr-case | schema | 333 | `async def get(self, case_id: str) -> HRCase │ None:` |
| app/services/runtime/sqlalchemy_adapters.py | schema-hr-case | schema | 338 | `return HRCase(` |
| app/services/runtime/sqlalchemy_adapters.py | schema-hr-case | schema | 355 | `async def upsert(self, case: HRCase) -> None:` |
| app/services/runtime/sqlalchemy_adapters.py | schema-hr-case | schema | 394 | `async def list(self, *, limit: int = 100) -> list[HRCase]:` |
| app/services/runtime/sqlalchemy_adapters.py | schema-hr-case | schema | 406 | `cases: list[HRCase] = []` |
| tests/unit/test_event_store.py | schema-hr-case | schema | 16 | `aggregate_type="hr_case",` |
| tests/unit/test_event_store.py | schema-hr-case | schema | 25 | `aggregate_type="hr_case",` |
| tests/unit/test_event_store.py | schema-hr-case | schema | 45 | `"aggregate_type": "hr_case",` |
| tests/unit/test_event_store.py | schema-hr-case | schema | 67 | `aggregate_type="hr_case",` |

## 干净文件

- `app/services/runtime/__init__.py`
- `app/services/runtime/clock.py`
- `app/services/runtime/event_store.py`
- `app/services/runtime/lease.py`
- `app/services/runtime/side_effects.py`
- `app/services/runtime/timer_coordinator.py`
- `app/services/runtime/timers.py`
