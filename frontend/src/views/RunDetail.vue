<!--
  RunDetail 页面：Agent Run 的审计视图。
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAgentRun } from '@/api/client'
import StepTimeline from '@/components/StepTimeline.vue'
import CitationPanel from '@/components/CitationPanel.vue'
import type { AgentRunDetail } from '@/types'

const route = useRoute()
const runId = route.params.id as string
const run = ref<AgentRunDetail | null>(null)
const loading = ref(true)
const activeTab = ref('steps')

onMounted(async () => {
  try {
    run.value = await getAgentRun(runId)
  } catch (e: unknown) {
    ElMessage.error(`获取 Run 详情失败: ${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})

function statusType(status: string) {
  if (status === 'completed') return 'success'
  if (status === 'failed' || status === 'cancelled') return 'danger'
  if (status === 'awaiting_approval') return 'warning'
  return 'info'
}

function formatTime(dateStr?: string | null) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="run-detail-page" v-loading="loading">
    <template v-if="run">
      <section class="surface run-hero">
        <div class="run-heading">
          <p class="section-kicker">Run audit</p>
          <h2>{{ run.original_query }}</h2>
          <div class="run-meta">
            <span class="mono">{{ run.id }}</span>
            <span>Thread: <b class="mono">{{ run.thread_id }}</b></span>
            <span>User: <b>{{ run.user_id }}</b></span>
          </div>
        </div>
        <el-tag :type="statusType(run.status)" size="large" effect="plain">
          {{ run.status }}
        </el-tag>
      </section>

      <section class="run-facts">
        <div class="fact-card">
          <span>创建时间</span>
          <strong>{{ formatTime(run.created_at) }}</strong>
        </div>
        <div class="fact-card">
          <span>完成时间</span>
          <strong>{{ formatTime(run.completed_at) }}</strong>
        </div>
        <div class="fact-card">
          <span>步骤</span>
          <strong>{{ run.steps.length }}</strong>
        </div>
        <div class="fact-card">
          <span>工具调用</span>
          <strong>{{ run.tool_calls.length }}</strong>
        </div>
      </section>

      <section class="surface run-body">
        <el-tabs v-model="activeTab">
          <el-tab-pane name="steps">
            <template #label>
              <span class="tab-label">
                <el-icon><List /></el-icon>
                执行步骤
              </span>
            </template>
            <StepTimeline :steps="run.steps" />
          </el-tab-pane>

          <el-tab-pane name="tools">
            <template #label>
              <span class="tab-label">
                <el-icon><Connection /></el-icon>
                工具调用
              </span>
            </template>
            <div v-if="run.tool_calls.length" class="record-list">
              <article
                v-for="(tc, idx) in run.tool_calls"
                :key="idx"
                class="record-card"
              >
                <div class="record-card-head">
                  <strong>{{ tc.tool_name }}</strong>
                  <el-tag
                    v-if="tc.risk_level"
                    :type="tc.risk_level === 'write' ? 'warning' : 'info'"
                    size="small"
                    effect="plain"
                  >
                    {{ tc.risk_level }}
                  </el-tag>
                </div>
                <pre class="json-block">{{ JSON.stringify(tc.parameters ?? {}, null, 2) }}</pre>
                <pre v-if="tc.result" class="json-block success">{{ JSON.stringify(tc.result, null, 2) }}</pre>
              </article>
            </div>
            <el-empty v-else description="暂无工具调用" :image-size="60" />
          </el-tab-pane>

          <el-tab-pane name="approvals">
            <template #label>
              <span class="tab-label">
                <el-icon><WarningFilled /></el-icon>
                审批记录
              </span>
            </template>
            <div v-if="run.approvals.length" class="record-list">
              <article
                v-for="approval in run.approvals"
                :key="approval.id"
                class="record-card"
              >
                <div class="record-card-head">
                  <strong>{{ approval.tool_name }}</strong>
                  <el-tag
                    :type="approval.decision === 'approve' ? 'success' : approval.decision === 'reject' ? 'danger' : 'warning'"
                    size="small"
                  >
                    {{ approval.decision ?? approval.status }}
                  </el-tag>
                </div>
                <pre v-if="approval.parameters" class="json-block">{{ JSON.stringify(approval.parameters, null, 2) }}</pre>
              </article>
            </div>
            <el-empty v-else description="暂无审批记录" :image-size="60" />
          </el-tab-pane>

          <el-tab-pane name="citations">
            <template #label>
              <span class="tab-label">
                <el-icon><DocumentCopy /></el-icon>
                引用来源
              </span>
            </template>
            <CitationPanel :citations="(run.result?.citations as any[]) ?? []" />
          </el-tab-pane>

          <el-tab-pane name="result">
            <template #label>
              <span class="tab-label">
                <el-icon><Finished /></el-icon>
                最终结果
              </span>
            </template>
            <pre v-if="run.result" class="json-block result-json">{{ JSON.stringify(run.result, null, 2) }}</pre>
            <el-empty v-else description="暂无结果" :image-size="60" />
          </el-tab-pane>
        </el-tabs>
      </section>
    </template>
  </div>
</template>

<style scoped>
.run-detail-page {
  display: grid;
  gap: 16px;
}

.run-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 20px;
}

.section-kicker {
  margin-bottom: 5px;
  color: var(--color-muted);
  font-size: 12px;
}

.run-heading h2 {
  max-width: 980px;
  color: var(--color-text);
  font-size: 22px;
  font-weight: 800;
  line-height: 1.35;
}

.run-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 12px;
  color: var(--color-muted);
  font-size: 12px;
}

.run-facts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.fact-card {
  min-width: 0;
  padding: 13px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.86);
}

.fact-card span,
.fact-card strong {
  display: block;
}

.fact-card span {
  color: var(--color-muted);
  font-size: 12px;
}

.fact-card strong {
  margin-top: 5px;
  overflow: hidden;
  color: var(--color-text);
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.run-body {
  padding: 6px 18px 18px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.record-list {
  display: grid;
  gap: 12px;
  padding-top: 6px;
}

.record-card {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #fff;
}

.record-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.json-block.success {
  border-color: #cbded6;
  background: var(--color-green-soft);
}

.result-json {
  max-height: 620px;
}

@media (max-width: 820px) {
  .run-hero {
    flex-direction: column;
  }

  .run-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
