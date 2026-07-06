/**
 * Agent Run Pinia Store。
 *
 * 管理当前 Agent Run 的状态、SSE 事件、审批列表。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AgentRunDetail, SSEEvent } from '@/types'
import { createAgentRun, getAgentRun, submitApproval } from '@/api/client'
import { streamAgentRun } from '@/api/sse'

export const useAgentStore = defineStore('agent', () => {
  // ── 状态 ──
  const currentRun = ref<AgentRunDetail | null>(null)
  const sseEvents = ref<SSEEvent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const sseCleanup = ref<(() => void) | null>(null)

  // ── 计算属性 ──

  /** 当前待审批列表（status=pending） */
  const pendingApprovals = computed(() => {
    if (!currentRun.value) return []
    return currentRun.value.approvals.filter((a: { status: string }) => a.status === 'pending')
  })

  /** 当前 Run 是否在等待审批 */
  const isAwaitingApproval = computed(() => {
    return currentRun.value?.status === 'awaiting_approval'
  })

  /** 当前 Run 是否已完成 */
  const isCompleted = computed(() => {
    return currentRun.value?.status === 'completed' || currentRun.value?.status === 'failed'
  })

  // ── 操作 ──

  /** 创建新的 Agent Run 并连接 SSE */
  async function startRun(query: string, userId: string = 'user_001') {
    sseCleanup.value?.()
    sseCleanup.value = null
    loading.value = true
    error.value = null
    sseEvents.value = []

    try {
      const res = await createAgentRun(query, userId)
      // 立即获取 Run 详情
      const detail = await getAgentRun(res.id)
      currentRun.value = detail

      // 连接 SSE 流
      const cleanup = streamAgentRun(res.id, (event: SSEEvent) => {
        sseEvents.value.push(event)
        // SSE 流结束后刷新 Run 详情
        if (event.type === 'run_status' || event.type === 'run_failed') {
          refreshRun(res.id)
        }
      })
      sseCleanup.value = cleanup

      return res.id
    } catch (e: unknown) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

  /** 刷新 Run 详情 */
  async function refreshRun(runId: string) {
    try {
      currentRun.value = await getAgentRun(runId)
    } catch (e: unknown) {
      console.warn('[AgentStore] 刷新 Run 失败:', (e as Error).message)
    }
  }

  /** 提交审批决策 */
  async function approve(runId: string, approvalId: string, decision: 'approve' | 'edit' | 'reject', editedParams?: Record<string, unknown>) {
    await submitApproval(runId, approvalId, {
      decision,
      edited_parameters: editedParams ?? null,
    })
    // 审批后刷新 Run
    await refreshRun(runId)
  }

  /** 断开 SSE、清空状态 */
  function reset() {
    sseCleanup.value?.()
    sseCleanup.value = null
    currentRun.value = null
    sseEvents.value = []
    error.value = null
    loading.value = false
  }

  return {
    currentRun,
    sseEvents,
    loading,
    error,
    pendingApprovals,
    isAwaitingApproval,
    isCompleted,
    startRun,
    refreshRun,
    approve,
    reset,
  }
})
