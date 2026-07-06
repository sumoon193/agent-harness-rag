/**
 * SSE（Server-Sent Events）封装。
 *
 * 对接后端 GET /agent-runs/{run_id}/stream 端点。
 * 后端每条事件格式：data: {"type":"...", "run_id":"...", "timestamp":"...", "data":{...}}\n\n
 */
import type { SSEEvent } from '@/types'

export type SSEEventHandler = (event: SSEEvent) => void

/**
 * 连接 SSE 流，返回清理函数。
 *
 * @param url     完整 SSE URL（如 /api/agent-runs/xxx/stream）
 * @param handler 每收到一条事件时的回调
 * @returns       关闭连接的函数
 */
export function connectSSE(url: string, handler: SSEEventHandler): () => void {
  const es = new EventSource(url)

  // SSE 标准事件：所有 data: 行都走 message 事件
  es.onmessage = (msg: MessageEvent<string>) => {
    try {
      const parsed = JSON.parse(msg.data) as SSEEvent
      handler(parsed)
    } catch {
      // 忽略无法解析的非标准消息，后端标准事件由测试覆盖。
    }
  }

  es.onerror = () => {
    es.close()
  }

  return () => es.close()
}

/** 订阅指定 Agent Run 的 SSE 流。 */
export function streamAgentRun(runId: string, handler: SSEEventHandler): () => void {
  return connectSSE(`/api/agent-runs/${runId}/stream`, handler)
}
