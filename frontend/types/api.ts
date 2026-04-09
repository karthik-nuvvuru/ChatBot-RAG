// Session Types
export interface Session {
  session_id: string
  user_id: string
  engagement_id: string | null
  project_id: string | null
  accelerator_type: 'basic' | 'advanced' | 'enterprise'
  conversation_metadata: Record<string, unknown>
  started_at: string
  last_active_at: string
  status: SessionStatus
  created_at: string
  updated_at: string
}

export type SessionStatus = 'active' | 'paused' | 'completed' | 'archived'

export interface SessionCreate {
  user_id: string
  engagement_id?: string
  project_id?: string
  accelerator_type?: 'basic' | 'advanced' | 'enterprise'
  conversation_metadata?: Record<string, unknown>
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
  has_more: boolean
}

// Message Types
export interface Message {
  message_id: string
  session_id: string
  role: MessageRole
  content: string
  message_metadata: Record<string, unknown>
  parent_message_id: string | null
  created_at: string
}

export type MessageRole = 'user' | 'assistant' | 'system'

export interface MessageCreate {
  role: MessageRole
  content: string
  message_metadata?: Record<string, unknown>
  parent_message_id?: string
}

export interface MessageListResponse {
  messages: Message[]
  total: number
  has_more: boolean
  next_cursor: string | null
}

export interface MessageThreadResponse {
  message: Message
  thread: Message[]
}

// Chat Types
export interface ChatRequest {
  session_id: string
  message: string
  stream?: boolean
  temperature?: number
  max_tokens?: number
}

export interface ChatResponse {
  session_id: string
  message_id: string
  content: string
  finish_reason: string
  usage?: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  }
}

// Action Types
export interface Action {
  action_id: string
  session_id: string
  message_id: string | null
  action_type: string
  action_metadata: Record<string, unknown>
  job_id: string | null
  logging_id: string | null
  workflow_id: string | null
  started_at: string | null
  completed_at: string | null
  status: ActionStatus
  result: Record<string, unknown>
  created_at: string
}

export type ActionStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface ActionListResponse {
  actions: Action[]
  total: number
}

export interface ActionResultResponse {
  action_id: string
  status: ActionStatus
  result: Record<string, unknown>
  completed_at: string | null
}

// Attachment Types
export interface Attachment {
  id: string
  filename: string
  content_type: string
  size: number
  url: string
  created_at: string
}

// WebSocket Types
export type WSMessageType =
  | 'user_message'
  | 'message_received'
  | 'stream_chunk'
  | 'message_complete'
  | 'typing_indicator'
  | 'typing_start'
  | 'typing_stop'
  | 'progress_update'
  | 'error'
  | 'pong'
  | 'ping'
  | 'system'

export interface WSMessage {
  type: WSMessageType
  payload?: Record<string, unknown>
  timestamp?: string
}

export interface WSUserMessage {
  type: 'user_message'
  content: string
  stream?: boolean
  timestamp?: string
}

export interface WSTypingStart {
  type: 'typing_start'
}

export interface WSTypingStop {
  type: 'typing_stop'
}

export interface WSPing {
  type: 'ping'
}

// API Error
export interface APIError {
  detail: string
  error_code?: string
}

// Health Check
export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  version: string
  env: 'dev' | 'prod'
  llm_provider: 'euri' | 'azure'
  services: {
    database: 'connected' | 'disconnected'
    redis: 'connected' | 'disconnected'
  }
}
