# API Reference

Complete API documentation for the Conversation AI Platform.

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints (except `/health`, `/`, and `/metrics`) require JWT Bearer authentication.

```
Authorization: Bearer <jwt_token>
```

### Obtaining a Token

Tokens are obtained via OAuth2 Password flow. The `tokenUrl` is:

```
POST /api/v1/auth/token
```

## Table of Contents

1. [Sessions API](#sessions-api)
2. [Messages API](#messages-api)
3. [Chat API](#chat-api)
4. [Actions API](#actions-api)
5. [System Endpoints](#system-endpoints)
6. [WebSocket](#websocket)
7. [Celery Scheduled Tasks](#celery-scheduled-tasks)

---

## Sessions API

### Create Session

Create a new conversation session.

```http
POST /api/v1/sessions
```

**Request Body:**

```json
{
  "user_id": "string (required)",
  "engagement_id": "string (optional)",
  "project_id": "string (optional)",
  "accelerator_type": "basic | advanced | enterprise (default: basic)",
  "conversation_metadata": {
    "key": "value"
  }
}
```

**Response (201):**

```json
{
  "session_id": "uuid",
  "user_id": "string",
  "engagement_id": "string | null",
  "project_id": "string | null",
  "accelerator_type": "string",
  "conversation_metadata": {},
  "started_at": "datetime",
  "last_active_at": "datetime",
  "status": "active | paused | completed | archived",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### List Sessions

List sessions with optional filtering.

```http
GET /api/v1/sessions
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string | No | - | Filter by user ID |
| `status` | string | No | - | Filter by status (active/paused/completed/archived) |
| `limit` | integer | No | 20 | Max results (1-100) |
| `offset` | integer | No | 0 | Pagination offset |

**Response (200):**

```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "user_id": "string",
      "engagement_id": "string | null",
      "project_id": "string | null",
      "accelerator_type": "string",
      "conversation_metadata": {},
      "started_at": "datetime",
      "last_active_at": "datetime",
      "status": "string",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ],
  "total": 100,
  "has_more": true
}
```

---

### Get Active Session Count

Get count of active sessions for current user.

```http
GET /api/v1/sessions/active/count
```

**Response (200):**

```json
{
  "count": 5
}
```

---

### Get Session

Get a specific session by ID.

```http
GET /api/v1/sessions/{session_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | uuid | Yes | Session UUID |

**Response (200):**

```json
{
  "session_id": "uuid",
  "user_id": "string",
  "engagement_id": "string | null",
  "project_id": "string | null",
  "accelerator_type": "string",
  "conversation_metadata": {},
  "started_at": "datetime",
  "last_active_at": "datetime",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### Update Session

Update session metadata or status.

```http
PATCH /api/v1/sessions/{session_id}
```

**Request Body:**

```json
{
  "status": "active | paused | completed | archived (optional)",
  "conversation_metadata": {
    "key": "value"
  }
}
```

**Response (200):**

```json
{
  "session_id": "uuid",
  "user_id": "string",
  "engagement_id": "string | null",
  "project_id": "string | null",
  "accelerator_type": "string",
  "conversation_metadata": {},
  "started_at": "datetime",
  "last_active_at": "datetime",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### Delete Session (Archive)

Archive a session (soft delete).

```http
DELETE /api/v1/sessions/{session_id}
```

**Response (204):** No content

---

### Fork Session

Fork an existing session to create a new one.

```http
POST /api/v1/sessions/{session_id}/fork
```

**Request Body:**

```json
{
  "new_user_id": "string (optional)"
}
```

**Response (201):**

```json
{
  "session_id": "uuid",
  "user_id": "string",
  "engagement_id": "string | null",
  "project_id": "string | null",
  "accelerator_type": "string",
  "conversation_metadata": {},
  "started_at": "datetime",
  "last_active_at": "datetime",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Messages API

### Add Message

Add a new message to a session.

```http
POST /api/v1/sessions/{session_id}/messages
```

**Request Body:**

```json
{
  "role": "user | assistant | system (required)",
  "content": "string (required, max 10000 chars)",
  "message_metadata": {
    "key": "value"
  },
  "parent_message_id": "uuid (optional)"
}
```

**Response (201):**

```json
{
  "message_id": "uuid",
  "session_id": "uuid",
  "role": "string",
  "content": "string",
  "message_metadata": {},
  "parent_message_id": "uuid | null",
  "created_at": "datetime"
}
```

---

### Get Session Messages

Get messages for a session with cursor pagination.

```http
GET /api/v1/sessions/{session_id}/messages
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Max results (1-100) |
| `cursor` | string | No | - | Pagination cursor |
| `role` | string | No | - | Filter by role |

**Response (200):**

```json
{
  "messages": [
    {
      "message_id": "uuid",
      "session_id": "uuid",
      "role": "string",
      "content": "string",
      "message_metadata": {},
      "parent_message_id": "uuid | null",
      "created_at": "datetime"
    }
  ],
  "total": 100,
  "has_more": true,
  "next_cursor": "string | null"
}
```

---

### Get Message

Get a specific message by ID.

```http
GET /api/v1/messages/{message_id}
```

**Response (200):**

```json
{
  "message_id": "uuid",
  "session_id": "uuid",
  "role": "string",
  "content": "string",
  "message_metadata": {},
  "parent_message_id": "uuid | null",
  "created_at": "datetime"
}
```

---

### Get Message Thread

Get a message and its thread of replies.

```http
GET /api/v1/messages/{message_id}/thread
```

**Response (200):**

```json
{
  "message": {
    "message_id": "uuid",
    "session_id": "uuid",
    "role": "string",
    "content": "string",
    "message_metadata": {},
    "parent_message_id": "uuid | null",
    "created_at": "datetime"
  },
  "thread": [
    {
      "message_id": "uuid",
      "session_id": "uuid",
      "role": "string",
      "content": "string",
      "message_metadata": {},
      "parent_message_id": "uuid | null",
      "created_at": "datetime"
    }
  ]
}
```

---

### Search Messages

Search messages within a session.

```http
GET /api/v1/sessions/{session_id}/messages/search?q=<query>&limit=20
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query |
| `limit` | integer | No | 20 | Max results (1-100) |

**Response (200):**

```json
{
  "results": [
    {
      "message_id": "uuid",
      "session_id": "uuid",
      "role": "string",
      "content": "string",
      "message_metadata": {},
      "parent_message_id": "uuid | null",
      "created_at": "datetime"
    }
  ],
  "total": 5
}
```

---

## Chat API

### Send Chat Message (Non-Streaming)

Send a message and get AI response.

```http
POST /api/v1/chat
```

**Request Body:**

```json
{
  "session_id": "uuid (required)",
  "message": "string (required, max 10000 chars)",
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**Response (200):**

```json
{
  "session_id": "uuid",
  "message_id": "uuid",
  "content": "string",
  "finish_reason": "string",
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

---

### Send Chat Message (Streaming)

Send a message and stream AI response.

```http
POST /api/v1/chat/stream
```

**Request Body:**

```json
{
  "session_id": "uuid (required)",
  "message": "string (required, max 10000 chars)",
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**Response (200):** Server-Sent Events (SSE) stream

```
data: {"type": "chunk", "content": "Hello"}
data: {"type": "chunk", "content": " world"}
data: {"type": "done", "message_id": "uuid", "content": "Hello world"}
```

---

## Actions API

Actions represent asynchronous operations like code execution, web searches, and API calls.

### List Session Actions

List actions for a session.

```http
GET /api/v1/actions/sessions/{session_id}/actions
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Max results (1-100) |
| `offset` | integer | No | 0 | Pagination offset |
| `status` | string | No | - | Filter by status (pending/running/completed/failed) |

**Response (200):**

```json
{
  "actions": [
    {
      "action_id": "uuid",
      "session_id": "uuid",
      "message_id": "uuid | null",
      "action_type": "string",
      "action_metadata": {},
      "job_id": "string | null",
      "logging_id": "string | null",
      "workflow_id": "string | null",
      "started_at": "datetime | null",
      "completed_at": "datetime | null",
      "status": "pending | running | completed | failed",
      "result": {},
      "created_at": "datetime"
    }
  ],
  "total": 10
}
```

---

### Get Action

Get a specific action by ID.

```http
GET /api/v1/actions/actions/{action_id}
```

**Response (200):**

```json
{
  "action_id": "uuid",
  "session_id": "uuid",
  "message_id": "uuid | null",
  "action_type": "string",
  "action_metadata": {},
  "job_id": "string | null",
  "logging_id": "string | null",
  "workflow_id": "string | null",
  "started_at": "datetime | null",
  "completed_at": "datetime | null",
  "status": "pending | running | completed | failed",
  "result": {},
  "created_at": "datetime"
}
```

---

### Get Action Result

Get the result of an action.

```http
GET /api/v1/actions/actions/{action_id}/result
```

**Response (200):**

```json
{
  "action_id": "uuid",
  "status": "completed | failed",
  "result": {
    "output": "string",
    "error": "string | null"
  },
  "completed_at": "datetime | null"
}
```

---

## System Endpoints

### Health Check

```http
GET /health
```

**Response (200):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "env": "dev | prod",
  "llm_provider": "euri | azure",
  "services": {
    "database": "connected",
    "redis": "connected"
  }
}
```

---

### Root

```http
GET /
```

**Response (200):**

```json
{
  "name": "Conversation AI Platform",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### Prometheus Metrics

```http
GET /metrics
```

**Response (200):** Prometheus text format

---

## WebSocket

### Real-Time Chat WebSocket

Connect to a WebSocket for real-time chat.

**Endpoint:**

```
ws://localhost:8000/api/v1/chat/sessions/{session_id}/ws?token=<jwt_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | JWT authentication token |
| `session_id` | path | Yes | Session UUID to connect to |

### WebSocket Message Types

#### Client to Server

**Send User Message:**

```json
{
  "type": "user_message",
  "content": "Hello, how are you?",
  "stream": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Typing Start:**

```json
{
  "type": "typing_start"
}
```

**Typing Stop:**

```json
{
  "type": "typing_stop"
}
```

**Ping:**

```json
{
  "type": "ping"
}
```

#### Server to Client

**Message Received Acknowledgment:**

```json
{
  "type": "message_received",
  "payload": {
    "content": "Hello, how are..."
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Stream Chunk:**

```json
{
  "type": "stream_chunk",
  "payload": {
    "content": "I'm doing well"
  },
  "done": false
}
```

**Message Complete:**

```json
{
  "type": "message_complete",
  "payload": {
    "message_id": "uuid",
    "content": "I'm doing well, thank you!"
  },
  "done": true
}
```

**Typing Indicator:**

```json
{
  "type": "typing_indicator",
  "payload": {
    "user_id": "user123",
    "is_typing": true
  }
}
```

**Progress Update:**

```json
{
  "type": "progress_update",
  "payload": {
    "progress": 50.0,
    "status": "processing",
    "message": "Searching..."
  }
}
```

**Error:**

```json
{
  "type": "error",
  "payload": {
    "code": "PROCESSING_ERROR",
    "message": "Failed to process message"
  }
}
```

**Pong:**

```json
{
  "type": "pong"
}
```

### WebSocket Close Codes

| Code | Reason | Description |
|------|--------|-------------|
| 4001 | Unauthorized | Invalid or missing token |
| 4002 | Connection failed | Could not establish connection |

---

## Celery Scheduled Tasks

The following tasks are scheduled via Celery Beat and executed by Celery Workers.

### Daily Session Archival

**Task:** `archive_inactive_sessions`
**Schedule:** Daily at 2:00 AM UTC
**Description:** Archives sessions that have been inactive for longer than `SESSION_INACTIVITY_THRESHOLD_DAYS` (default: 30 days).

**Behavior:**
1. Queries sessions with status `ACTIVE` and `last_active_at` older than threshold
2. Updates status to `ARCHIVED` in batches
3. Logs archive count

**Returns:**
```json
{
  "archived_count": 15
}
```

---

### Weekly Attachment Cleanup

**Task:** `cleanup_old_attachments`
**Schedule:** Weekly on Sunday at 3:00 AM UTC
**Description:** Deletes attachments older than `ATTACHMENT_CLEANUP_DAYS` retention period.

**Behavior:**
1. Scans local storage `/app/storage/attachments`
2. Deletes files with modification time older than retention threshold
3. Logs deleted count and bytes freed

**Returns:**
```json
{
  "deleted_count": 42,
  "freed_bytes": 104857600
}
```

---

### Abandoned Session Cleanup

**Task:** `cleanup_abandoned_sessions`
**Schedule:** Manual trigger
**Description:** Removes sessions in `PAUSED` status for more than 30 days.

**Behavior:**
1. Queries sessions with status `PAUSED` and `last_active_at` older than 30 days
2. Permanently deletes these sessions

**Returns:**
```json
{
  "deleted_count": 5
}
```

---

### Session Metrics Update

**Task:** `update_session_metrics`
**Trigger:** Per-session, async
**Description:** Updates metrics for a specific session.

**Parameters:**
```json
{
  "session_id": "uuid-string"
}
```

**Returns:**
```json
{
  "session_id": "uuid-string",
  "status": "updated"
}
```

---

### Attachment Virus Scan

**Task:** `scan_attachments_for_viruses`
**Trigger:** Per-attachment upload
**Description:** Placeholder for virus scanning (production: integrate ClamAV).

**Parameters:**
```json
{
  "attachment_path": "/app/storage/attachments/file.pdf"
}
```

**Returns:**
```json
{
  "path": "/app/storage/attachments/file.pdf",
  "status": "clean",
  "scanned_at": "2024-01-15T10:30:00Z"
}
```

---

### Attachment Integrity Verification

**Task:** `verify_attachment_integrity`
**Trigger:** Per-attachment
**Description:** Verifies attachment exists and size is valid after upload.

**Parameters:**
```json
{
  "attachment_path": "/app/storage/attachments/file.pdf"
}
```

**Returns:**
```json
{
  "path": "/app/storage/attachments/file.pdf",
  "exists": true,
  "size": 1048576,
  "verified_at": "2024-01-15T10:30:00Z"
}
```

---

### Thumbnail Generation

**Task:** `generate_thumbnail`
**Trigger:** Per-image attachment
**Description:** Generates thumbnail for image attachments.

**Parameters:**
```json
{
  "attachment_path": "/app/storage/attachments/image.jpg"
}
```

**Returns:**
```json
{
  "path": "/app/storage/attachments/image.jpg",
  "thumbnail_path": "/app/storage/attachments/image.jpg.thumb",
  "generated_at": "2024-01-15T10:30:00Z"
}
```

---

### Action Execution

**Task:** `execute_action`
**Trigger:** Per-action request
**Description:** Executes an action asynchronously (code execution, web search, API call).

**Parameters:**
```json
{
  "action_id": "uuid-string",
  "action_type": "code_execution | web_search | api_call",
  "params": {
    "code": "print('hello')",
    "query": "search term",
    "endpoint": "https://api.example.com"
  }
}
```

**Returns:**
```json
{
  "status": "completed",
  "action_id": "uuid-string",
  "output": "string or results array or response object"
}
```

---

### Action Progress Streaming

**Task:** `stream_action_progress`
**Trigger:** During action execution
**Description:** Streams action progress to WebSocket clients.

**Parameters:**
```json
{
  "action_id": "uuid-string",
  "progress": 50.0
}
```

**Returns:**
```json
{
  "action_id": "uuid-string",
  "progress": 50.0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Action Completion Notification

**Task:** `notify_action_complete`
**Trigger:** After action completes
**Description:** Notifies clients that an action has completed.

**Parameters:**
```json
{
  "action_id": "uuid-string",
  "result": {
    "output": "results",
    "status": "success"
  }
}
```

**Returns:**
```json
{
  "action_id": "uuid-string",
  "completed_at": "2024-01-15T10:30:00Z",
  "result": {}
}
```

---

### Action Rollback

**Task:** `rollback_action`
**Trigger:** On action failure
**Description:** Rolls back a failed action.

**Parameters:**
```json
{
  "action_id": "uuid-string",
  "reason": "Timeout exceeded"
}
```

**Returns:**
```json
{
  "action_id": "uuid-string",
  "rolled_back_at": "2024-01-15T10:30:00Z",
  "reason": "Timeout exceeded"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Role 'admin' required"
}
```

### 404 Not Found

```json
{
  "detail": "Session not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 429 Rate Limited

```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error

```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "An internal error occurred",
  "details": null
}
```

---

## Enums

### AcceleratorTypeEnum

| Value | Description |
|-------|-------------|
| `basic` | Basic accelerator |
| `advanced` | Advanced accelerator |
| `enterprise` | Enterprise accelerator |

### MessageRoleEnum

| Value | Description |
|-------|-------------|
| `user` | User message |
| `assistant` | AI assistant message |
| `system` | System message |

### SessionStatusEnum

| Value | Description |
|-------|-------------|
| `active` | Session is active |
| `paused` | Session is paused |
| `completed` | Session completed normally |
| `archived` | Session archived (soft deleted) |

### ActionStatus

| Value | Description |
|-------|-------------|
| `pending` | Action not yet started |
| `running` | Action in progress |
| `completed` | Action completed successfully |
| `failed` | Action failed |

---

## Rate Limits

Default rate limits (configurable via environment):

| Endpoint | Limit |
|----------|-------|
| `/api/v1/chat` | 60 requests/minute/user |
| `/api/v1/chat/stream` | 30 requests/minute/user |
| Other authenticated endpoints | 100 requests/minute/user |

---

*Generated for v1.0.0*
