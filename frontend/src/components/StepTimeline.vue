<!--
  StepTimeline 组件：Agent 执行步骤和 SSE 事件。
-->
<script setup lang="ts">
import type { AgentStep, SSEEvent } from '@/types'

defineProps<{
  steps: AgentStep[]
  sseEvents?: SSEEvent[]
}>()

function stepColor(nodeName: string): string {
  if (nodeName.includes('intent')) return '#245b9b'
  if (nodeName.includes('retrieve') || nodeName.includes('retriev')) return '#1f6f5b'
  if (nodeName.includes('plan')) return '#a86618'
  if (nodeName.includes('approval') || nodeName.includes('approve')) return '#b42318'
  if (nodeName.includes('tool') || nodeName.includes('execute')) return '#5d6470'
  if (nodeName.includes('answer') || nodeName.includes('generate')) return '#2f4858'
  return '#8b96a5'
}

function formatTime(dateStr?: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('zh-CN')
}
</script>

<template>
  <div class="step-timeline" data-testid="step-timeline">
    <header v-if="steps.length > 0" class="timeline-title">
      <span>
        <el-icon><List /></el-icon>
        执行步骤
      </span>
      <b>{{ steps.length }}</b>
    </header>

    <ol v-if="steps.length > 0" class="timeline-list">
      <li
        v-for="(step, idx) in steps"
        :key="idx"
        class="timeline-item"
        :style="{ '--step-color': stepColor(step.node_name) }"
      >
        <div class="step-marker" />
        <div class="step-body">
          <div class="step-head">
            <strong>{{ step.node_name }}</strong>
            <span v-if="step.duration_ms != null">{{ step.duration_ms }}ms</span>
            <time v-if="step.completed_at">{{ formatTime(step.completed_at) }}</time>
          </div>
          <pre v-if="step.output_data" class="json-block step-output">{{ JSON.stringify(step.output_data, null, 2) }}</pre>
        </div>
      </li>
    </ol>

    <template v-if="sseEvents && sseEvents.length > 0">
      <header class="timeline-title live-title">
        <span>
          <el-icon><Connection /></el-icon>
          实时事件
        </span>
        <b>{{ sseEvents.length }}</b>
      </header>
      <ol class="timeline-list live-list">
        <li
          v-for="(event, idx) in sseEvents"
          :key="idx"
          class="timeline-item"
          :style="{ '--step-color': stepColor(event.type) }"
        >
          <div class="step-marker" />
          <div class="step-body">
            <div class="step-head">
              <strong>{{ event.type }}</strong>
              <time>{{ new Date(event.timestamp).toLocaleTimeString('zh-CN') }}</time>
            </div>
            <pre v-if="event.data" class="json-block step-output">{{ JSON.stringify(event.data, null, 2) }}</pre>
          </div>
        </li>
      </ol>
    </template>

    <el-empty
      v-if="steps.length === 0 && (!sseEvents || sseEvents.length === 0)"
      description="暂无执行步骤"
      :image-size="60"
    />
  </div>
</template>

<style scoped>
.step-timeline {
  display: grid;
  gap: 12px;
}

.timeline-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--color-text);
  font-size: 14px;
  font-weight: 800;
}

.timeline-title span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.timeline-title b {
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--color-primary-strong);
  background: var(--color-green-soft);
  font-size: 12px;
}

.live-title {
  margin-top: 8px;
}

.timeline-list {
  display: grid;
  gap: 10px;
  list-style: none;
}

.timeline-item {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  gap: 10px;
}

.step-marker {
  width: 10px;
  height: 10px;
  margin-top: 13px;
  border: 2px solid #ffffff;
  border-radius: 999px;
  background: var(--step-color);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--step-color) 18%, transparent);
}

.step-body {
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #ffffff;
}

.step-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.step-head strong {
  color: var(--color-text);
  font-size: 13px;
}

.step-head span,
.step-head time {
  color: var(--color-muted);
  font-size: 11px;
}

.step-output {
  max-height: 180px;
  margin-top: 9px;
}
</style>
