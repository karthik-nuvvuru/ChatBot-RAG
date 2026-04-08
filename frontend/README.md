# NelloreRuchullu Frontend

A modern, production-ready chatbot web application UI built with Next.js, TypeScript, and Tailwind CSS.

## Features

- **Real-time Streaming**: Live streaming responses via WebSocket
- **Session Management**: Create, switch, and manage chat sessions
- **Markdown Support**: Full markdown rendering with syntax highlighting
- **File Attachments**: Upload and preview files
- **Dark Theme**: Beautiful dark mode UI
- **Responsive Design**: Works on desktop and mobile
- **Optimistic Updates**: Instant UI feedback

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **WebSocket**: Native WebSocket API
- **Testing**: Jest + React Testing Library

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Run the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── chat/[sessionId]/     # Chat session page
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Landing page
├── components/              # React components
│   ├── chat/                # Chat components
│   │   ├── ChatWindow.tsx   # Main chat window
│   │   ├── MessageBubble.tsx # Message display
│   │   ├── ChatInput.tsx   # Message input
│   │   └── TypingIndicator.tsx
│   └── sidebar/             # Sidebar components
├── lib/                     # Utilities and API
│   ├── api.ts              # REST API client
│   ├── websocket.ts         # WebSocket client
│   ├── utils.ts            # Helper functions
│   └── hooks/              # Custom hooks
├── types/                   # TypeScript types
└── tests/                   # Test files
```

## API Integration

The frontend integrates with the NelloreRuchullu backend API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sessions` | GET | List sessions |
| `/api/v1/sessions` | POST | Create session |
| `/api/v1/sessions/{id}` | DELETE | Delete session |
| `/api/v1/sessions/{id}/messages` | GET | Get messages |
| `/api/v1/sessions/{id}/messages` | POST | Send message |
| `/api/v1/chat` | POST | Send chat message |
| `/api/v1/chat/stream` | POST | Stream chat response |

## WebSocket

Connect to WebSocket at:
```
ws://localhost:8000/api/v1/chat/sessions/{sessionId}/ws?token={jwt}
```

### Message Types

**Client → Server:**
- `user_message` - Send a message
- `typing_start` / `typing_stop` - Typing indicators
- `ping` - Heartbeat

**Server → Client:**
- `message_received` - Message acknowledged
- `stream_chunk` - Streaming response chunk
- `message_complete` - Full response ready
- `typing_indicator` - Other user typing
- `error` - Error occurred

## Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run test     # Run tests
npm run lint     # Run ESLint
```

## Testing

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch
```

## License

MIT
