/**
 * useSSE 组合式函数。
 *
 * 封装 EventSource 连接，返回响应式事件列表。
 * 自动在组件卸载时断开连接。
 */
import { ref, onUnmounted } from 'vue'
import type { SSEEvent } from '@/types'

export function useSSE() {
  const events = ref<SSEEvent[]>([])
  const connected = ref(false)
  let eventSource: EventSource | null = null

  /** 连接 SSE 流 */
  function connect(url: string, onEvent?: (event: SSEEvent) => void) {
    // 清理已有连接
    disconnect()
    events.value = []
    connected.value = true

    eventSource = new EventSource(url)

    eventSource.onmessage = (msg: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(msg.data) as SSEEvent
        events.value.push(parsed)
        onEvent?.(parsed)
      } catch {
        console.warn('[useSSE] 无法解析:', msg.data)
      }
    }

    eventSource.onerror = () => {
      connected.value = false
      eventSource?.close()
    }
  }

  /** 断开连接 */
  function disconnect() {
    eventSource?.close()
    eventSource = null
    connected.value = false
  }

  onUnmounted(disconnect)

  return { events, connected, connect, disconnect }
}
