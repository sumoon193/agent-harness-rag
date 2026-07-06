<!--
  EvalResult 页面：RAGAS / Agent 指标的操作看板。
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { runEval } from '@/api/client'
import type { EvalRunResponse } from '@/types'

const datasetPath = ref('')
const running = ref(false)
const result = ref<EvalRunResponse | null>(null)

const rows = computed(() => {
  if (!result.value) return []
  return Object.entries(result.value.metrics).map(([name, value]) => ({
    name,
    value,
    percentage: Math.round(value * 100),
  }))
})

async function handleRunEval() {
  running.value = true
  result.value = null

  try {
    result.value = await runEval(datasetPath.value || undefined)
    ElMessage.success('评测完成')
  } catch (e: unknown) {
    ElMessage.error(`评测失败: ${(e as Error).message}`)
  } finally {
    running.value = false
  }
}

function metricTone(value: number) {
  if (value >= 0.8) return 'strong'
  if (value >= 0.6) return 'middle'
  return 'weak'
}
</script>

<template>
  <div class="eval-page">
    <section class="surface eval-runner">
      <div>
        <p class="section-kicker">Evaluation</p>
        <h2>运行 Golden Dataset 评测</h2>
      </div>

      <div class="runner-form">
        <el-input
          v-model="datasetPath"
          placeholder="留空使用默认 Golden Dataset"
          clearable
        >
          <template #prepend>Dataset</template>
        </el-input>
        <el-button type="primary" :loading="running" @click="handleRunEval">
          <el-icon><VideoPlay /></el-icon>
          运行评测
        </el-button>
      </div>
    </section>

    <section v-if="result" class="surface result-surface">
      <header class="result-header">
        <div>
          <p class="section-kicker">Result</p>
          <h2>{{ result.message }}</h2>
          <span class="mono">{{ result.run_id }}</span>
        </div>
        <el-tag :type="result.status === 'completed' ? 'success' : 'info'" size="large" effect="plain">
          {{ result.status }}
        </el-tag>
      </header>

      <div class="metric-grid">
        <article
          v-for="row in rows"
          :key="row.name"
          :class="['metric-card', metricTone(row.value)]"
        >
          <span>{{ row.name }}</span>
          <strong>{{ row.percentage }}%</strong>
          <div class="bar-track">
            <i :style="{ width: `${row.percentage}%` }" />
          </div>
        </article>
      </div>

      <el-table :data="rows" class="metric-table" border>
        <el-table-column prop="name" label="指标" min-width="220" />
        <el-table-column prop="value" label="数值" width="140">
          <template #default="{ row }">
            {{ row.value.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column label="百分比" min-width="220">
          <template #default="{ row }">
            <el-progress
              :percentage="row.percentage"
              :color="row.percentage >= 80 ? '#1f6f5b' : row.percentage >= 60 ? '#a86618' : '#b42318'"
            />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-else class="surface eval-empty">
      <el-icon><TrendCharts /></el-icon>
      <span>评测结果会在这里形成指标快照</span>
    </section>
  </div>
</template>

<style scoped>
.eval-page {
  display: grid;
  gap: 16px;
}

.eval-runner,
.result-surface,
.eval-empty {
  padding: 20px;
}

.eval-runner {
  display: grid;
  grid-template-columns: minmax(260px, 360px) minmax(0, 1fr);
  gap: 24px;
  align-items: end;
}

.section-kicker {
  margin-bottom: 5px;
  color: var(--color-muted);
  font-size: 12px;
}

.eval-runner h2,
.result-header h2 {
  color: var(--color-text);
  font-size: 20px;
  font-weight: 800;
  line-height: 1.35;
}

.runner-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.result-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

.result-header .mono {
  display: inline-block;
  margin-top: 8px;
  color: var(--color-muted);
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.metric-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: #ffffff;
}

.metric-card span {
  overflow: hidden;
  color: var(--color-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-card strong {
  color: var(--color-text);
  font-size: 24px;
  line-height: 1;
}

.bar-track {
  height: 5px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5ebf0;
}

.bar-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.metric-card.strong .bar-track i {
  background: var(--color-primary);
}

.metric-card.middle .bar-track i {
  background: var(--color-amber);
}

.metric-card.weak .bar-track i {
  background: var(--color-red);
}

.metric-table {
  width: 100%;
}

.eval-empty {
  display: grid;
  place-items: center;
  min-height: 260px;
  gap: 10px;
  color: var(--color-muted);
}

.eval-empty .el-icon {
  color: var(--color-primary);
  font-size: 38px;
}

@media (max-width: 1080px) {
  .eval-runner,
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .eval-runner,
  .runner-form,
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
