# API Reference - NelloreRuchullu Conversation AI Platform

## Overview

Base URL: `http://localhost:8000` (development)
API Version: v1
API Prefix: `/api/v1`

## Authentication

All authenticated endpoints require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are obtained via the `/auth/token` endpoint. The token contains:
- `sub`: user_id
- `email`: user email (optional)
- `roles`: array of roles (e.g., `["user"]`)
- `exp`: expiration timestamp

### Getting a Token

**Request:**
```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "user_id": "karthik123",
  "email": "karthik123@example.com"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJrYXJ0aGlrMTIzIiwiZW1haWwiOiJrYXJ0aGlrMTIzQGV4YW1wbGUuY29tIiwicm9sZXMiOlsidXNlciJdLCJleHAiOjE3NzU3NjAxNTcsImlhdCI6MTc3NTc1ODM1N30.wR1Axu7nvNgniUBGpJoZLkGGPwruizRY7ozwHzON1DY",
  "token_type": "bearer"
}
```

**Error (400 - Missing user_id):**
```json
{
  "detail": "user_id is required"
}
```

---

## Sessions API

### Create Session

Creates a new conversation session.

**Request:**
```http
POST /api/v1/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "karthik123"
}
```

**Response (201 Created):**
```json
{
  "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
  "user_id": "karthik123",
  "engagement_id": null,
  "project_id": null,
  "accelerator_type": "basic",
  "conversation_metadata": {},
  "started_at": "2026-04-09T18:30:00.123456",
  "last_active_at": "2026-04-09T18:30:00.123456",
  "status": "active",
  "created_at": "2026-04-09T18:30:00.123456",
  "updated_at": "2026-04-09T18:30:00.123456"
}
```

**UI Trigger:** User clicks "New Chat" button → `useCreateSession().mutateAsync()` called → navigates to `/chat/{session_id}`

---

### List Sessions

Lists all sessions for the authenticated user.

**Request:**
```http
GET /api/v1/sessions?limit=20&offset=0
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | null | Filter by status (active, paused, completed, archived) |
| `limit` | integer | 20 | Number of results (1-100) |
| `offset` | integer | 0 | Pagination offset |

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
      "user_id": "karthik123",
      "engagement_id": null,
      "project_id": null,
      "accelerator_type": "basic",
      "conversation_metadata": {},
      "started_at": "2026-04-09T18:30:00.123456",
      "last_active_at": "2026-04-09T18:30:00.123456",
      "status": "active",
      "created_at": "2026-04-09T18:30:00.123456",
      "updated_at": "2026-04-09T18:30:00.123456"
    }
  ],
  "total": 1,
  "has_more": false
}
```

**UI Trigger:** Sidebar component loads → `useSessions()` hook fetches on mount

---

### Get Session

Gets a specific session by ID.

**Request:**
```http
GET /api/v1/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
  "user_id": "karthik123",
  "engagement_id": null,
  "project_id": null,
  "accelerator_type": "basic",
  "conversation_metadata": {},
  "started_at": "2026-04-09T18:30:00.123456",
  "last_active_at": "2026-04-09T18:30:00.123456",
  "status": "active",
  "created_at": "2026-04-09T18:30:00.123456",
  "updated_at": "2026-04-09T18:30:00.123456"
}
```

**Error (404 Not Found):**
```json
{
  "detail": "Session not found"
}
```

**Error (403 Forbidden):**
```json
{
  "detail": "Access denied"
}
```

**UI Trigger:** Chat page loads with sessionId in URL → `useSession(sessionId)` fetches session data

---

### Update Session

Updates session status or metadata.

**Request:**
```http
PATCH /api/v1/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "paused"
}
```

**Response (200 OK):**
```json
{
  "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
  "user_id": "karthik123",
  "status": "paused",
  ...
}
```

---

### Delete Session (Archive)

Archives a session (soft delete).

**Request:**
```http
DELETE /api/v1/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea
Authorization: Bearer <token>
```

**Response (204 No Content)**

**UI Trigger:** User clicks delete on session in sidebar → `useDeleteSession().mutateAsync()` called

---

### Fork Session

Creates a copy of an existing session.

**Request:**
```http
POST /api/v1/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea/fork
Authorization: Bearer <token>
Content-Type: application/json

{
  "new_user_id": "another_user"
}
```

**Response (201 Created):**
```json
{
  "session_id": "new-session-uuid",
  "user_id": "another_user",
  "status": "active",
  ...
}
```

---

### Get Active Session Count

**Request:**
```http
GET /api/v1/sessions/active/count
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "active_sessions": 5
}
```

---

## Messages API

### Add Message

Adds a new message to a session.

**Request:**
```http
POST /api/v1/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "role": "user",
  "content": "Hello, how are you?"
}
```

**Request Body Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | yes | One of: `user`, `assistant`, `system` |
| `content` | string | yes | Message content (1-10000 chars) |
| `parent_message_id` | UUID | no | Parent message for threading |
| `message_metadata` | object | no | Additional metadata |

**Response (201 Created):**
```json
{
  "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
  "role": "user",
  "content": "Hello, how are you?",
  "message_metadata": {},
  "parent_message_id": null,
  "created_at": "2026-04-09T18:31:00.123456"
}
```

**Error (404 - Session not found):**
```json
{
  "detail": "Session f14dcb09-7ba0-4850-92af-f94eb6b241ea not found"
}
```

**Error (400 - Session not active):**
```json
{
  "detail": "Session f14dcb09-7ba0-4850-92af-f94eb6b241ea is not active"
}
```

**UI Trigger:** This endpoint is called internally by the orchestrator when processing chat messages, not directly by UI

---

### Get Session Messages

Gets paginated messages for a session.

**Request:**
```http
GET /api/v1/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea/messages?limit=20&cursor=abc123
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Results per page (1-100) |
| `cursor` | string | null | Pagination cursor from previous response |
| `role` | string | null | Filter by role (user, assistant, system) |

**Response (200 OK):**
```json
{
  "messages": [
    {
      "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
      "role": "user",
      "content": "Hello, how are you?",
      "message_metadata": {},
      "parent_message_id": null,
      "created_at": "2026-04-09T18:31:00.123456"
    },
    {
      "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
      "role": "assistant",
      "content": "I'm doing well! How can I help you today?",
      "message_metadata": {},
      "parent_message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2026-04-09T18:31:01.234567"
    }
  ],
  "total": 2,
  "has_more": false,
  "next_cursor": null
}
```

**UI Trigger:** Chat page loads → `useMessages(sessionId)` fetches message history via infinite query

---

### Search Messages

Full-text search within a session's messages.

**Request:**
```http
GET /api/v1/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea/messages/search?q=hello&limit=10
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | yes | Search query (min 1 char) |
| `limit` | integer | 20 | Max results (1-100) |

**Response (200 OK):**
```json
{
  "messages": [...],
  "query": "hello",
  "count": 1
}
```

---

### Get Message Thread

Gets a message and its reply chain.

**Request:**
```http
GET /api/v1/messages/a1b2c3d4-e5f6-7890-abcd-ef1234567890/thread
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "message": {
    "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
    "role": "user",
    "content": "Hello",
    ...
  },
  "thread": [
    {
      "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "role": "assistant",
      "content": "Hi there!",
      ...
    }
  ]
}
```

---

## Chat API

### Send Message (Non-Streaming)

Sends a message and returns a complete AI response.

**Request:**
```http
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
  "message": "Hello, how are you?",
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**Request Body Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | UUID | yes | Target session |
| `message` | string | yes | User message (1-10000 chars) |
| `stream` | boolean | no | Ignored for this endpoint (always false) |
| `temperature` | float | no | LLM temperature (0.0-2.0, default 0.7) |
| `max_tokens` | integer | no | Max response tokens (1-32768, default 4096) |

**Response (200 OK):**
```json
{
  "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
  "message_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "content": "I'm doing well! How can I help you today?",
  "finish_reason": "stop",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 50,
    "total_tokens": 200
  }
}
```

**UI Trigger:** Not used by frontend - UI uses WebSocket for streaming responses

---

### Send Message (Streaming)

Streams AI response chunks using Server-Sent Events (SSE).

**Request:**
```http
POST /api/v1/chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "f14dcb09-7ba0-4850-92af-f94eb6b241ea",
  "message": "Hello, how are you?",
  "stream": true
}
```

**Response (200 OK):**
```
Content-Type: text/event-stream

data: {"chunk": "I"}

data: {"chunk": "'m"}

data: {"chunk": " doing"}

data: {"chunk": " well"}

...
```

**UI Trigger:** Not used by frontend - UI uses WebSocket instead

---

## WebSocket API

### Connect to Chat Session

Real-time bidirectional communication for chat.

**Connection URL:**
```
ws://localhost:8000/api/v1/chat/sessions/{session_id}/ws?token={jwt_token}
```

**Example:**
```
ws://localhost:8000/api/v1/chat/sessions/f14dcb09-7ba0-4850-92af-f94eb6b241ea/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**UI Trigger:** Chat page loads → `wsClient.connect()` called in `useChat` hook

---

### WebSocket Message Types

#### Client → Server Messages

**Send User Message:**
```json
{
  "type": "user_message",
  "content": "Hello, how are you?",
  "stream": true,
  "timestamp": "2026-04-09T18:32:00.000000"
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

**Ping (Heartbeat):**
```json
{
  "type": "ping"
}
```

#### Server → Client Messages

**Message Received (Ack):**
```json
{
  "type": "message_received",
  "payload": {
    "content": "Hello, how are you?"
  },
  "timestamp": "2026-04-09T18:32:00.000000"
}
```

**Stream Chunk:**
```json
{
  "type": "stream_chunk",
  "payload": {
    "content": "I'm"
  },
  "done": false
}
```

**Message Complete:**
```json
{
  "type": "message_complete",
  "payload": {
    "message_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "content": "I'm doing well! How can I help you today?"
  },
  "done": true
}
```

**Typing Indicator:**
```json
{
  "type": "typing_indicator",
  "payload": {
    "user_id": "karthik123",
    "is_typing": true
  }
}
```

**Error:**
```json
{
  "type": "error",
  "payload": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session does not exist or user lacks access",
    "retry_after": 5
  }
}
```

**Pong (Heartbeat Response):**
```json
{
  "type": "pong"
}
```

---

### WebSocket Connection Flow

```
1. Frontend: wsClient.connect({ sessionId, token })
2. Backend: WebSocket handshake → validate token → accept()
3. Backend: connection_manager.connect(websocket, session_id, user_id)
4. Frontend: onStatusChange('connected')
5. Frontend: wsClient.sendUserMessage("Hello")
6. Backend: handle_message() → orchestrator.process_message()
7. Backend: stream_callback(chunk) → send stream_chunk
8. Frontend: onStreamChunk(chunk) → update streamingContent state
9. Backend: completion → send message_complete
10. Frontend: onMessageReceived(completeMessage) → add to messages list
11. Frontend: setIsSending(false)
```

---

## UI Interaction Flows

### Flow 1: User Opens App

```
1. User navigates to http://localhost:3000
2. Home page checks: getStoredToken() exists?
   - NO → redirect to /login
   - YES → continue
3. Home page renders with "New Chat" button
```

### Flow 2: User Logs In

```
1. User enters user_id (email optional)
2. POST /api/v1/auth/token { user_id, email }
3. Response: { access_token, token_type }
4. Token stored in localStorage 'auth_token'
5. Redirect to home page
```

### Flow 3: User Creates New Chat

```
1. User clicks "New Chat" button
2. POST /api/v1/sessions { user_id }
3. Response: { session_id: "uuid-...", ... }
4. Navigate to /chat/{session_id}
5. WebSocket connects to /api/v1/chat/sessions/{session_id}/ws?token=...
6. Sidebar loads sessions: GET /api/v1/sessions
7. Chat window shows empty state with suggestions
```

### Flow 4: User Sends Message

```
1. User types message in ChatInput
2. User presses Enter or clicks Send
3. handleSend() called with message text
4. useChat.sendMessage() invoked
5. if (!wsClient.isConnected()) → show error, don't send
6. Create optimistic user message
7. onMessageReceived(optimisticMessage) → UI shows message immediately
8. wsClient.sendUserMessage(content) → WebSocket sends user_message
9. Backend receives → orchestrator processes
10. Backend streams chunks → stream_chunk events
11. Frontend updates streamingContent state → UI shows streaming text
12. Backend sends message_complete
13. Frontend: onMessageReceived(completeMessage) → replace optimistic + add assistant
14. Frontend: setIsSending(false)
```

### Flow 5: User Switches Chats

```
1. User clicks session in Sidebar
2. handleSessionSelect(newSessionId) called
3. setCurrentSessionId(newSessionId)
4. ChatWindow receives new sessionId prop
5. useEffect: WebSocket disconnects from old session
6. useEffect: WebSocket connects to new session
7. Messages fetched via useMessages(newSessionId)
8. Chat window renders with loaded messages
```

### Flow 6: Page Reload with Active Session

```
1. Page loads /chat/{session_id}
2. Auth check: token exists?
3. Session ID validated (must be valid UUID)
4. WebSocket connects with sessionId
5. useSession(sessionId) fetches session
6. useMessages(sessionId) fetches message history
7. ChatWindow renders with messages
8. WebSocket ready for sending/receiving
```

---

## Error Handling

### HTTP Status Codes

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| 200 | OK | Successful GET, PATCH |
| 201 | Created | Successful POST (create) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input, validation failure |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User doesn't own resource |
| 404 | Not Found | Session/message not found |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Backend failure |

### Error Response Format

```json
{
  "detail": "Human-readable error message"
}
```

Or for structured errors:
```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "The requested session does not exist",
  "details": {}
}
```

### Frontend Error Handling

```typescript
// API client interceptor handles 401 automatically
this.client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired - refresh and retry
      localStorage.removeItem('auth_token')
      const newToken = await ensureAuthToken()
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`
        return this.client(error.config)
      }
    }
    return Promise.reject(error)
  }
)

// WebSocket error handling
wsClient.connect({
  onError: (error: string) => {
    console.error('WebSocket error:', error)
    onError?.('Connection error occurred')
  }
})
```

---

## Data Models

### Session

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | UUID | Unique identifier |
| `user_id` | string | Owner user ID |
| `engagement_id` | string\|null | Optional engagement reference |
| `project_id` | string\|null | Optional project reference |
| `accelerator_type` | string | basic\|advanced\|enterprise |
| `conversation_metadata` | object | Custom metadata |
| `status` | string | active\|paused\|completed\|archived |
| `started_at` | datetime | Session start time |
| `last_active_at` | datetime | Last activity time |
| `created_at` | datetime | Creation time |
| `updated_at` | datetime | Last update time |

### Message

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | UUID | Unique identifier |
| `session_id` | UUID | Parent session |
| `role` | string | user\|assistant\|system |
| `content` | string | Message text (max 10000 chars) |
| `message_metadata` | object | Custom metadata |
| `parent_message_id` | UUID\|null | For threading |
| `created_at` | datetime | Creation time |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `user_message` | C→S | User sends message |
| `message_received` | S→C | Server acknowledges receipt |
| `stream_chunk` | S→C | Partial response content |
| `message_complete` | S→C | Full response delivered |
| `typing_start` | C→S | User started typing |
| `typing_stop` | C→S | User stopped typing |
| `typing_indicator` | S→C | Another user typing |
| `ping` | C→S | Heartbeat |
| `pong` | S→C | Heartbeat response |
| `error` | S→C | Error occurred |

---

## Notes for Frontend Developers

### Important UUID Validation

The frontend WebSocket client validates session IDs before connecting:

```typescript
const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
if (!uuidRegex.test(sessionId)) {
  console.log('WebSocket: Invalid sessionId, skipping connect:', sessionId)
  return
}
```

If the sessionId is "new" or invalid, WebSocket connection is skipped.

### Message Deduplication

When `message_complete` is received with a `message_id` that matches the pending optimistic message ID, the frontend discards the optimistic message and uses the real one from the server instead.

### Streaming State Management

The streaming cursor animation uses `animate-cursor` CSS class with `background-color: var(--primary)`.

### ChatInput Never Disabled

The ChatInput component always has `disabled={false}`. The WebSocket connection state is handled separately - if not connected, `sendMessage()` shows a warning but the UI remains usable.

### Axios Interceptor Logic

The API client automatically:
1. Gets token from localStorage on each request
2. If no token, calls `ensureAuthToken()` to fetch one
3. Attaches `Authorization: Bearer <token>` header
4. On 401 response, removes old token, fetches new one, retries request

### WebSocket Reconnection

The WebSocket client uses exponential backoff:
- Attempt 1: 3s delay
- Attempt 2: 6s delay
- Attempt 3: 12s delay
- Max 5 attempts by default

### CSS Variables for Theming

```css
--background: #020617;
--card: #111827;
--foreground: #f8fafc;
--muted: #94a3b8;
--primary: #3b82f6;
--accent: #8b5cf6;
--border: #1e293b;
```

### Required Environment Variables

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**Backend (.env):**
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/conversation_ai
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secret-key
EURI_API_KEY=your-api-key
```
