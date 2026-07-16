<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createCase,
  decideCaseApproval,
  getCaseEvents,
  getRuntimeMetrics,
  listCases,
  refreshCasePolicy,
  startCase,
} from '@/api/client'
import type { CaseEvent, HRCase, RuntimeMetricsSnapshot } from '@/types'

const cases = ref<HRCase[]>([])
const selected = ref<HRCase | null>(null)
const events = ref<CaseEvent[]>([])
const metrics = ref<RuntimeMetricsSnapshot | null>(null)
const loading = ref(false)
const mutating = ref(false)

const pendingApproval = computed(() => {
  const approvals = selected.value?.working_memory?.approvals
  if (!Array.isArray(approvals)) return null
  return [...approvals].reverse().find((item: any) => item.status === 'pending') ?? null
})

const toolResult = computed(() => {
  const results = selected.value?.working_memory?.tool_results
  return Array.isArray(results) && results.length ? results[results.length - 1] : null
})

const timer = computed(() => {
  const timers = selected.value?.working_memory?.timers
  return Array.isArray(timers) && timers.length ? timers[timers.length - 1] : null
})

const phaseSteps = computed(() => [
  { label: 'Research', done: Boolean(selected.value?.working_memory?.evidence) },
  { label: 'Plan', done: Boolean(selected.value?.working_memory?.plan) },
  { label: 'Approval', done: Boolean(selected.value?.working_memory?.approvals) },
  { label: 'Action', done: Boolean(toolResult.value) },
  { label: 'Timer', done: Boolean(timer.value) },
])

async function refreshQueue(selectId?: string) {
  cases.value = await listCases()
  const target = selectId ?? selected.value?.id ?? cases.value[0]?.id
  if (target) {
    const item = cases.value.find((candidate) => candidate.id === target) ?? cases.value[0]
    await selectCase(item)
  } else {
    selected.value = null
    events.value = []
  }
}

async function refreshMetrics() {
  metrics.value = await getRuntimeMetrics()
}

async function selectCase(item: HRCase) {
  selected.value = item
  events.value = (await getCaseEvents(item.id)).items
}

async function handleCreate() {
  mutating.value = true
  try {
    const created = await createCase()
    await Promise.all([refreshQueue(created.id), refreshMetrics()])
    ElMessage.success('Case 已创建')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    mutating.value = false
  }
}

async function handleStart() {
  if (!selected.value) return
  mutating.value = true
  try {
    const updated = await startCase(selected.value)
    await Promise.all([refreshQueue(updated.id), refreshMetrics()])
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    mutating.value = false
  }
}

async function handleDecision(decision: 'approve' | 'reject') {
  if (!selected.value || !pendingApproval.value) return
  mutating.value = true
  try {
    const updated = await decideCaseApproval(
      selected.value,
      pendingApproval.value.approval_id,
      decision,
    )
    await Promise.all([refreshQueue(updated.id), refreshMetrics()])
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    mutating.value = false
  }
}

async function handlePolicyRefresh() {
  if (!selected.value) return
  mutating.value = true
  try {
    const current = selected.value.policy_versions?.hr_policy ?? 'v1'
    const numeric = Number(current.match(/(\d+)$/)?.[1] ?? 1) + 1
    const updated = await refreshCasePolicy(selected.value, `v${numeric}`)
    await Promise.all([refreshQueue(updated.id), refreshMetrics()])
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    mutating.value = false
  }
}

function statusType(status: string) {
  if (status === 'waiting_approval') return 'warning'
  if (status === 'waiting_timer') return 'success'
  if (status === 'failed' || status === 'cancelled') return 'danger'
  return 'info'
}

function eventTone(type: string) {
  if (type.includes('approval')) return 'approval'
  if (type.includes('evidence') || type.includes('a2a')) return 'evidence'
  if (type.includes('tool')) return 'tool'
  if (type.includes('timer')) return 'timer'
  return 'neutral'
}

function formatDate(value?: string) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function counter(name: string) {
  return metrics.value?.counters?.[name] ?? 0
}

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([refreshQueue(), refreshMetrics()])
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="case-console" v-loading="loading">
    <section class="metric-band" data-testid="runtime-metrics">
      <div>
        <span>Active cases</span>
        <strong>{{ cases.filter((item) => !['completed', 'cancelled'].includes(item.status)).length }}</strong>
      </div>
      <div>
        <span>Awaiting approval</span>
        <strong>{{ cases.filter((item) => item.status === 'waiting_approval').length }}</strong>
      </div>
      <div>
        <span>Unsafe writes</span>
        <strong class="safe-value">{{ counter('runtime.unsafe_tool_execution.total') }}</strong>
      </div>
      <div>
        <span>Duplicate effects</span>
        <strong class="safe-value">{{ counter('runtime.side_effects.duplicate') }}</strong>
      </div>
      <div>
        <span>A2A / MCP</span>
        <strong>{{ counter('runtime.protocol.a2a.success') }} / {{ counter('runtime.protocol.mcp.success') }}</strong>
      </div>
    </section>

    <div class="operations-grid">
      <aside class="case-queue surface">
        <header class="queue-header">
          <div>
            <span>WORK QUEUE</span>
            <strong>Long-running cases</strong>
          </div>
          <el-tooltip content="创建入职 Case" placement="bottom">
            <el-button
              type="primary"
              circle
              :loading="mutating"
              aria-label="新建 Case"
              @click="handleCreate"
            >
              <el-icon><Plus /></el-icon>
            </el-button>
          </el-tooltip>
        </header>

        <div v-if="cases.length" class="queue-list">
          <button
            v-for="item in cases"
            :key="item.id"
            type="button"
            :class="['queue-item', { active: selected?.id === item.id }]"
            @click="selectCase(item)"
          >
            <span class="queue-item-top">
              <b>{{ item.title }}</b>
              <i :class="`status-dot status-dot--${item.status}`" />
            </span>
            <span class="queue-subject">{{ item.subject_user_id }}</span>
            <span class="queue-meta">
              <em>{{ item.status }}</em>
              <time>v{{ item.version }}</time>
            </span>
          </button>
        </div>

        <div v-else class="queue-empty">
          <el-icon><Briefcase /></el-icon>
          <strong>No active cases</strong>
          <span>创建 Reference Case 以启动治理流程。</span>
          <el-button type="primary" :loading="mutating" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建入职 Case
          </el-button>
        </div>
      </aside>

      <main v-if="selected" class="case-detail" data-testid="case-detail">
        <header class="case-heading">
          <div>
            <p class="case-kicker">HR SHARED SERVICE / {{ selected.id }}</p>
            <h2>{{ selected.title }}</h2>
            <div class="case-identifiers">
              <span>Subject <b>{{ selected.subject_user_id }}</b></span>
              <span>Run <b class="mono">{{ selected.active_run_id ?? 'not started' }}</b></span>
              <span>Policy <b>{{ selected.execution_manifest.policy_version }}</b></span>
            </div>
          </div>
          <div class="case-actions">
            <el-tag :type="statusType(selected.status)" effect="dark">
              {{ selected.status }}
            </el-tag>
            <el-button
              v-if="selected.status === 'open' && !selected.active_run_id"
              type="primary"
              :loading="mutating"
              @click="handleStart"
            >
              <el-icon><VideoPlay /></el-icon>
              启动治理流程
            </el-button>
            <el-button
              v-if="selected.status === 'waiting_timer'"
              :loading="mutating"
              @click="handlePolicyRefresh"
            >
              <el-icon><Refresh /></el-icon>
              模拟制度更新
            </el-button>
          </div>
        </header>

        <div class="phase-track" aria-label="Case phase">
          <div v-for="(step, index) in phaseSteps" :key="step.label" :class="{ done: step.done }">
            <span>{{ index + 1 }}</span>
            <b>{{ step.label }}</b>
          </div>
        </div>

        <div class="case-body">
          <section class="timeline-region" data-testid="artifact-timeline">
            <header class="region-header">
              <div>
                <span>ARTIFACT TIMELINE</span>
                <strong>Persistent event stream</strong>
              </div>
              <b>{{ events.length }} events</b>
            </header>

            <ol class="artifact-list">
              <li v-for="event in events" :key="event.id" :class="`artifact artifact--${eventTone(event.event_type)}`">
                <div class="event-sequence">{{ String(event.sequence).padStart(2, '0') }}</div>
                <div class="event-content">
                  <header>
                    <strong>{{ event.event_type }}</strong>
                    <time>{{ formatDate(event.created_at) }}</time>
                  </header>
                  <p>{{ event.actor_id }}</p>
                  <pre>{{ JSON.stringify(event.payload, null, 2) }}</pre>
                </div>
              </li>
            </ol>
          </section>

          <aside class="governance-region">
            <section v-if="pendingApproval" class="approval-gate" data-testid="case-approval">
              <header>
                <el-icon><Lock /></el-icon>
                <div>
                  <span>HUMAN GATE</span>
                  <strong>{{ pendingApproval.tool_name }}</strong>
                </div>
              </header>
              <dl>
                <div><dt>Revision</dt><dd>{{ pendingApproval.revision }}</dd></div>
                <div><dt>Policy</dt><dd>{{ pendingApproval.policy_version }}</dd></div>
                <div><dt>Expires</dt><dd>{{ formatDate(pendingApproval.expires_at) }}</dd></div>
              </dl>
              <code>{{ pendingApproval.subject_hash }}</code>
              <div class="gate-actions">
                <el-button type="success" :loading="mutating" @click="handleDecision('approve')">
                  <el-icon><Check /></el-icon>
                  批准并恢复
                </el-button>
                <el-button type="danger" plain :disabled="mutating" @click="handleDecision('reject')">
                  <el-icon><Close /></el-icon>
                  拒绝
                </el-button>
              </div>
            </section>

            <section class="governance-block">
              <header><span>EXECUTION MANIFEST</span><el-icon><Stamp /></el-icon></header>
              <dl>
                <div><dt>Model</dt><dd>{{ selected.execution_manifest.model_name }}</dd></div>
                <div><dt>Skill</dt><dd>{{ selected.working_memory?.skill?.version ?? 'not loaded' }}</dd></div>
                <div><dt>Retrieval</dt><dd>{{ selected.execution_manifest.retrieval_version }}</dd></div>
                <div><dt>Context</dt><dd>{{ selected.execution_manifest.context_strategy_version }}</dd></div>
              </dl>
            </section>

            <section v-if="toolResult" class="governance-block result-block">
              <header><span>SIDE EFFECT LEDGER</span><el-icon><CircleCheck /></el-icon></header>
              <strong>{{ toolResult.result?.ticket_id }}</strong>
              <pre>{{ JSON.stringify(toolResult.result, null, 2) }}</pre>
            </section>

            <section v-if="timer" class="governance-block">
              <header><span>DURABLE TIMER</span><el-icon><Timer /></el-icon></header>
              <dl>
                <div><dt>Type</dt><dd>{{ timer.timer_type }}</dd></div>
                <div><dt>Due</dt><dd>{{ formatDate(timer.due_at) }}</dd></div>
                <div><dt>Status</dt><dd>{{ timer.status }}</dd></div>
              </dl>
            </section>
          </aside>
        </div>
      </main>

      <main v-else class="case-detail empty-detail">
        <el-icon><Files /></el-icon>
        <h2>Case queue is empty</h2>
        <p>创建一个入职到转正 Case，验证证据、审批、恢复、幂等和审计。</p>
      </main>
    </div>
  </div>
</template>

<style scoped>
.case-console { display: grid; gap: 14px; }
.metric-band { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid var(--color-border); background: #fff; }
.metric-band > div { min-width: 0; padding: 12px 15px; border-right: 1px solid var(--color-border-soft); }
.metric-band > div:last-child { border-right: 0; }
.metric-band span, .metric-band strong { display: block; }
.metric-band span { color: var(--color-muted); font-size: 11px; text-transform: uppercase; }
.metric-band strong { margin-top: 5px; font-family: 'Cascadia Mono', Consolas, monospace; font-size: 19px; }
.safe-value { color: var(--color-primary); }
.operations-grid { display: grid; grid-template-columns: 286px minmax(0, 1fr); min-height: calc(100vh - 210px); border-top: 1px solid var(--color-border); }
.case-queue { align-self: stretch; border-radius: 0; box-shadow: none; }
.queue-header { display: flex; align-items: center; justify-content: space-between; padding: 15px; border-bottom: 1px solid var(--color-border); }
.queue-header span, .queue-header strong { display: block; }
.queue-header span, .region-header span, .governance-block header span, .approval-gate header span { color: var(--color-muted); font-size: 10px; font-weight: 800; }
.queue-header strong { margin-top: 3px; font-size: 14px; }
.queue-list { display: grid; }
.queue-item { width: 100%; padding: 14px 15px; border: 0; border-bottom: 1px solid var(--color-border-soft); color: inherit; background: #fff; text-align: left; cursor: pointer; }
.queue-item:hover, .queue-item.active { background: #eef5f2; }
.queue-item.active { box-shadow: inset 3px 0 var(--color-primary); }
.queue-item-top, .queue-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.queue-item-top b { overflow: hidden; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.queue-subject { display: block; margin: 6px 0 9px; color: var(--color-muted); font-size: 12px; }
.queue-meta { color: var(--color-subtle); font-size: 10px; }
.queue-meta em { overflow: hidden; font-style: normal; text-transform: uppercase; text-overflow: ellipsis; }
.status-dot { width: 7px; height: 7px; flex: 0 0 auto; border-radius: 50%; background: #8b96a5; }
.status-dot--waiting_approval { background: #d58a21; }
.status-dot--waiting_timer { background: #1f8a68; }
.queue-empty { display: grid; justify-items: center; gap: 8px; padding: 50px 20px; text-align: center; }
.queue-empty > .el-icon { font-size: 28px; color: var(--color-primary); }
.queue-empty span { color: var(--color-muted); font-size: 12px; line-height: 1.5; }
.case-detail { min-width: 0; background: #fff; border-right: 1px solid var(--color-border); }
.case-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 22px; padding: 20px 22px 16px; border-bottom: 1px solid var(--color-border); }
.case-kicker { color: var(--color-muted); font-size: 10px; font-weight: 800; }
.case-heading h2 { margin-top: 5px; font-size: 21px; line-height: 1.25; }
.case-identifiers { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 11px; color: var(--color-muted); font-size: 11px; }
.case-identifiers b { color: var(--color-text); }
.case-actions { display: flex; align-items: center; gap: 9px; }
.phase-track { display: grid; grid-template-columns: repeat(5, minmax(80px, 1fr)); padding: 13px 22px; border-bottom: 1px solid var(--color-border); background: #f8faf9; }
.phase-track > div { position: relative; display: flex; align-items: center; gap: 7px; color: var(--color-subtle); font-size: 11px; }
.phase-track > div::after { position: absolute; top: 50%; right: 10px; left: 32px; height: 1px; background: var(--color-border); content: ''; z-index: 0; }
.phase-track > div:last-child::after { display: none; }
.phase-track span, .phase-track b { position: relative; z-index: 1; background: #f8faf9; }
.phase-track span { display: grid; place-items: center; width: 20px; height: 20px; border: 1px solid var(--color-border); border-radius: 50%; }
.phase-track b { padding-right: 8px; }
.phase-track .done { color: var(--color-primary-strong); }
.phase-track .done span { color: #fff; border-color: var(--color-primary); background: var(--color-primary); }
.case-body { display: grid; grid-template-columns: minmax(0, 1fr) 326px; }
.timeline-region { min-width: 0; padding: 18px 22px 28px; }
.region-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.region-header span, .region-header strong { display: block; }
.region-header strong { margin-top: 3px; font-size: 14px; }
.region-header > b { color: var(--color-muted); font: 11px 'Cascadia Mono', Consolas, monospace; }
.artifact-list { display: grid; gap: 8px; list-style: none; }
.artifact { display: grid; grid-template-columns: 36px minmax(0, 1fr); border: 1px solid var(--color-border-soft); border-left: 3px solid #8b96a5; background: #fff; }
.artifact--approval { border-left-color: #b66d12; }
.artifact--evidence { border-left-color: #1f6f5b; }
.artifact--tool { border-left-color: #245b9b; }
.artifact--timer { border-left-color: #7a5b9e; }
.event-sequence { display: grid; place-items: start center; padding-top: 12px; color: var(--color-subtle); font: 10px 'Cascadia Mono', Consolas, monospace; background: #f7f9fa; }
.event-content { min-width: 0; padding: 10px 12px; }
.event-content header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.event-content header strong { font: 12px 'Cascadia Mono', Consolas, monospace; }
.event-content time, .event-content p { color: var(--color-muted); font-size: 10px; }
.event-content p { margin-top: 3px; }
.event-content pre, .governance-block pre { max-height: 128px; overflow: auto; margin-top: 8px; color: #435063; font: 10px/1.45 'Cascadia Mono', Consolas, monospace; white-space: pre-wrap; }
.governance-region { min-width: 0; border-left: 1px solid var(--color-border); background: #f8fafb; }
.approval-gate, .governance-block { padding: 16px; border-bottom: 1px solid var(--color-border); }
.approval-gate { background: #fff8ed; }
.approval-gate header { display: flex; align-items: center; gap: 9px; }
.approval-gate header > .el-icon { color: #a86618; font-size: 20px; }
.approval-gate header span, .approval-gate header strong { display: block; }
.approval-gate header strong { margin-top: 2px; font-size: 13px; }
.approval-gate code { display: block; overflow: hidden; margin-top: 10px; color: var(--color-muted); font-size: 9px; text-overflow: ellipsis; }
.gate-actions { display: flex; gap: 6px; margin-top: 12px; }
.governance-block header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 11px; color: var(--color-primary); }
.governance-block dl, .approval-gate dl { display: grid; gap: 7px; }
.governance-block dl > div, .approval-gate dl > div { display: grid; grid-template-columns: 82px minmax(0, 1fr); gap: 8px; font-size: 10px; }
.governance-block dt, .approval-gate dt { color: var(--color-muted); }
.governance-block dd, .approval-gate dd { overflow-wrap: anywhere; color: var(--color-text); }
.result-block { background: #eef7f3; }
.result-block > strong { color: var(--color-primary-strong); font: 15px 'Cascadia Mono', Consolas, monospace; }
.empty-detail { display: grid; place-content: center; justify-items: center; gap: 9px; color: var(--color-muted); text-align: center; }
.empty-detail > .el-icon { color: var(--color-primary); font-size: 36px; }
.empty-detail h2 { color: var(--color-text); font-size: 18px; }
.empty-detail p { max-width: 460px; font-size: 12px; }
@media (max-width: 1240px) { .case-body { grid-template-columns: 1fr; } .governance-region { border-top: 1px solid var(--color-border); border-left: 0; } }
@media (max-width: 900px) { .metric-band { grid-template-columns: repeat(2, 1fr); } .operations-grid { grid-template-columns: 1fr; } .case-queue { max-height: 340px; overflow-y: auto; } .case-heading { flex-direction: column; } }
@media (max-width: 620px) { .metric-band { grid-template-columns: 1fr; } .metric-band > div { border-right: 0; border-bottom: 1px solid var(--color-border-soft); } .phase-track { grid-template-columns: 1fr; gap: 7px; } .phase-track > div::after { display: none; } .case-actions { align-items: flex-start; flex-direction: column; } .event-content header { align-items: flex-start; flex-direction: column; } }
</style>
