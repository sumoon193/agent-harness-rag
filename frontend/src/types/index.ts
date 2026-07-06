/**
 * 前端 TypeScript 类型定义。
 *
 * 对齐后端 app/api/schemas.py 中的 Pydantic schema。
 */

// ── 枚举 ──────────────────────────────────────────────────────────────

/** Agent Run 状态（对齐 RunStatus 枚举） */
export type RunStatus =
  | 'created'
  | 'running'
  | 'retrieving_evidence'
  | 'planning'
  | 'awaiting_approval'
  | 'resumed'
  | 'completed'
  | 'failed'
  | 'cancelled'

/** 文档入库状态 */
export type DocumentStatus = 'pending' | 'parsing' | 'chunking' | 'indexing' | 'ready' | 'failed'

/** 审批决策类型 */
export type ApprovalDecisionType = 'approve' | 'edit' | 'reject'

// ── Health ─────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
  mode: string
  services: Record<string, HealthService>
}

export interface HealthService {
  status: string
  error?: string
  [key: string]: unknown
}

// ── Document ───────────────────────────────────────────────────────────

export interface DocumentCreateResponse {
  id: string
  task_id: string
  status: string
  message: string
}

export interface IngestionStatusResponse {
  task_id: string
  document_id: string
  status: string
  progress: number
  error_message: string | null
}

// ── Agent Run ──────────────────────────────────────────────────────────

export interface AgentRunCreateRequest {
  query: string
  user_id: string
}

export interface AgentRunCreateResponse {
  id: string
  thread_id: string
  status: RunStatus
  message: string
}

export interface AgentRunDetail {
  id: string
  user_id: string
  thread_id: string
  original_query: string
  status: RunStatus
  steps: AgentStep[]
  tool_calls: ToolCallRecord[]
  approvals: ApprovalRecord[]
  result: Record<string, unknown> | null
  created_at: string
  completed_at: string | null
}

export interface AgentStep {
  node_name: string
  input_data?: Record<string, unknown>
  output_data?: Record<string, unknown>
  started_at?: string
  completed_at?: string
  duration_ms?: number
}

export interface ToolCallRecord {
  tool_name: string
  parameters?: Record<string, unknown>
  result?: Record<string, unknown>
  risk_level?: string
  requires_approval?: boolean
}

export interface ApprovalRecord {
  id: string
  tool_name: string
  parameters?: Record<string, unknown>
  status: string
  decision?: string
  risk_level?: string
  created_at?: string
}

// ── Approval ───────────────────────────────────────────────────────────

export interface ApprovalSubmitRequest {
  decision: ApprovalDecisionType
  edited_parameters?: Record<string, unknown> | null
}

export interface ApprovalSubmitResponse {
  approval_id: string
  status: string
  decision: string
}

// ── Eval ───────────────────────────────────────────────────────────────

export interface EvalRunRequest {
  dataset_path?: string | null
}

export interface EvalRunResponse {
  run_id: string
  status: string
  metrics: Record<string, number>
  message: string
}

// ── SSE 事件 ───────────────────────────────────────────────────────────

export interface SSEEvent {
  type: string
  run_id: string
  timestamp: string
  data: Record<string, unknown>
}

// ── 聊天消息（前端内部使用） ──────────────────────────────────────────

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  runId?: string
  timestamp: Date
}
