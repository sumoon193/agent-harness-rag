<!--
  ApprovalCard 组件：写入型工具调用的人工审批。
-->
<script setup lang="ts">
import { ref } from 'vue'
import type { ApprovalRecord } from '@/types'

const props = defineProps<{
  approval: ApprovalRecord
  runId: string
}>()

const emit = defineEmits<{
  decide: [decision: 'approve' | 'edit' | 'reject', editedParams?: Record<string, unknown>]
}>()

const showEditDialog = ref(false)
const editedJson = ref('')

function handleApprove() {
  emit('decide', 'approve')
}

function handleReject() {
  emit('decide', 'reject')
}

function openEditDialog() {
  editedJson.value = JSON.stringify(props.approval.parameters ?? {}, null, 2)
  showEditDialog.value = true
}

function submitEdit() {
  try {
    const params = JSON.parse(editedJson.value)
    emit('decide', 'edit', params)
    showEditDialog.value = false
  } catch {
    return
  }
}

function riskType(level?: string) {
  if (level === 'write') return 'warning'
  if (level === 'admin') return 'danger'
  return 'info'
}
</script>

<template>
  <section class="approval-card" data-testid="approval-card">
    <header class="approval-header">
      <div>
        <span class="approval-kicker">Approval required</span>
        <strong>{{ approval.tool_name }}</strong>
      </div>
      <el-tag :type="riskType(approval.risk_level)" effect="plain" size="small">
        {{ approval.risk_level ?? 'read' }}
      </el-tag>
    </header>

    <div class="approval-meta">
      <span>Run</span>
      <b class="mono">{{ runId }}</b>
    </div>

    <pre class="json-block params-block">{{ JSON.stringify(approval.parameters ?? {}, null, 2) }}</pre>

    <div class="approval-actions">
      <el-button type="success" @click="handleApprove">
        <el-icon><Check /></el-icon>
        Approve
      </el-button>
      <el-button type="warning" plain @click="openEditDialog">
        <el-icon><Edit /></el-icon>
        Edit
      </el-button>
      <el-button type="danger" plain @click="handleReject">
        <el-icon><Close /></el-icon>
        Reject
      </el-button>
    </div>

    <el-dialog v-model="showEditDialog" title="编辑工具参数" width="520px">
      <el-input
        v-model="editedJson"
        type="textarea"
        :rows="9"
        placeholder="JSON 参数"
      />
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">提交编辑</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.approval-card {
  display: grid;
  gap: 12px;
  margin: 12px 0;
  padding: 14px;
  border: 1px solid #d9c49f;
  border-left: 4px solid var(--color-amber);
  border-radius: var(--radius);
  background: #fffaf2;
}

.approval-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.approval-kicker,
.approval-header strong {
  display: block;
}

.approval-kicker {
  margin-bottom: 3px;
  color: var(--color-amber);
  font-size: 11px;
  font-weight: 800;
}

.approval-header strong {
  color: var(--color-text);
  font-size: 14px;
}

.approval-meta {
  display: grid;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid rgba(168, 102, 24, 0.2);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.72);
}

.approval-meta span {
  color: var(--color-muted);
  font-size: 11px;
}

.approval-meta b {
  overflow: hidden;
  color: var(--color-text);
  font-size: 12px;
  text-overflow: ellipsis;
}

.params-block {
  max-height: 220px;
}

.approval-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
