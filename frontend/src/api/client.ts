/**
 * Typed API Client。
 *
 * 封装后端 FastAPI 8 个端点的调用，所有请求走 Vite proxy（/api → localhost:8000）。
 */
import type {
  HealthResponse,
  DocumentCreateResponse,
  IngestionStatusResponse,
  AgentRunCreateResponse,
  AgentRunDetail,
  ApprovalSubmitRequest,
  ApprovalSubmitResponse,
  EvalRunResponse,
} from '@/types'

const BASE = '/api'

/** 通用 fetch wrapper，统一错误处理 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  return res.json() as Promise<T>
}

// ── Health ─────────────────────────────────────────────────────────────

/** GET /health */
export function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

// ── Documents ──────────────────────────────────────────────────────────

/** POST /documents — multipart/form-data 文件上传 */
export async function uploadDocument(
  file: File,
  tenantId: string,
  departmentId: string,
  visibility: string = 'department',
): Promise<DocumentCreateResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('tenant_id', tenantId)
  form.append('department_id', departmentId)
  form.append('visibility', visibility)

  const res = await fetch(`${BASE}/documents`, { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  return res.json()
}

// ── Ingestion ──────────────────────────────────────────────────────────

/** GET /ingestions/{taskId} */
export function getIngestionTask(taskId: string): Promise<IngestionStatusResponse> {
  return request<IngestionStatusResponse>(`/ingestions/${taskId}`)
}

// ── Agent Runs ─────────────────────────────────────────────────────────

/** POST /agent-runs */
export function createAgentRun(query: string, userId: string): Promise<AgentRunCreateResponse> {
  return request<AgentRunCreateResponse>('/agent-runs', {
    method: 'POST',
    body: JSON.stringify({ query, user_id: userId }),
  })
}

/** GET /agent-runs/{runId} */
export function getAgentRun(runId: string): Promise<AgentRunDetail> {
  return request<AgentRunDetail>(`/agent-runs/${runId}`)
}

// ── Approvals ──────────────────────────────────────────────────────────

/** POST /agent-runs/{runId}/approvals/{approvalId} */
export function submitApproval(
  runId: string,
  approvalId: string,
  body: ApprovalSubmitRequest,
): Promise<ApprovalSubmitResponse> {
  return request<ApprovalSubmitResponse>(`/agent-runs/${runId}/approvals/${approvalId}`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// ── Eval ───────────────────────────────────────────────────────────────

/** POST /eval/runs */
export function runEval(datasetPath?: string): Promise<EvalRunResponse> {
  return request<EvalRunResponse>('/eval/runs', {
    method: 'POST',
    body: JSON.stringify({ dataset_path: datasetPath ?? null }),
  })
}
