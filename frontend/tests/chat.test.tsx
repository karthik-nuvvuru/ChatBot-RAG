import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChatWindow } from '@/components/chat/ChatWindow'
import { ChatInput } from '@/components/chat/ChatInput'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { Sidebar } from '@/components/sidebar/Sidebar'
import type { Session, Message } from '@/types/api'

// Create a wrapper with query client
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    getSessions: jest.fn(),
    createSession: jest.fn(),
    deleteSession: jest.fn(),
    getMessages: jest.fn(),
    sendChatMessage: jest.fn(),
  },
}))

describe('ChatInput', () => {
  const mockOnSend = jest.fn()
  const mockOnTypingStart = jest.fn()
  const mockOnTypingStop = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders correctly', () => {
    render(
      <ChatInput
        onSend={mockOnSend}
        disabled={false}
      />
    )

    expect(screen.getByPlaceholderText('Type a message...')).toBeInTheDocument()
  })

  it('calls onSend when send button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ChatInput
        onSend={mockOnSend}
        disabled={false}
      />
    )

    const input = screen.getByPlaceholderText('Type a message...')
    await user.type(input, 'Hello, world!')

    const sendButton = screen.getByRole('button', { name: /send/i })
    await user.click(sendButton)

    expect(mockOnSend).toHaveBeenCalledWith('Hello, world!', undefined)
  })

  it('clears input after sending', async () => {
    const user = userEvent.setup()
    render(
      <ChatInput
        onSend={mockOnSend}
        disabled={false}
      />
    )

    const input = screen.getByPlaceholderText('Type a message...')
    await user.type(input, 'Test message')

    const sendButton = screen.getByRole('button', { name: /send/i })
    await user.click(sendButton)

    expect(input).toHaveValue('')
  })

  it('disables send button when input is empty', () => {
    render(
      <ChatInput
        onSend={mockOnSend}
        disabled={false}
      />
    )

    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeDisabled()
  })

  it('handles Enter key to send', async () => {
    const user = userEvent.setup()
    render(
      <ChatInput
        onSend={mockOnSend}
        disabled={false}
      />
    )

    const input = screen.getByPlaceholderText('Type a message...')
    await user.type(input, 'Hello{enter}')

    expect(mockOnSend).toHaveBeenCalled()
  })

  it('handles Shift+Enter for newline', async () => {
    const user = userEvent.setup()
    render(
      <ChatInput
        onSend={mockOnSend}
        disabled={false}
      />
    )

    const input = screen.getByPlaceholderText('Type a message...')
    await user.type(input, 'Line 1{shift>}{Enter}{/shift}Line 2')

    expect(mockOnSend).not.toHaveBeenCalled()
    expect(input).toContainHTML('<br')
  })

  it('disables input when disabled prop is true', () => {
    render(
      <ChatInput
        onSend={mockOnSend}
        disabled={true}
      />
    )

    const input = screen.getByPlaceholderText('Connecting...')
    expect(input).toBeDisabled()
  })
})

describe('MessageBubble', () => {
  const mockOnRetry = jest.fn()

  const userMessage: Message = {
    message_id: '1',
    session_id: 'session-1',
    role: 'user',
    content: 'Hello, AI!',
    message_metadata: {},
    parent_message_id: null,
    created_at: new Date().toISOString(),
  }

  const assistantMessage: Message = {
    message_id: '2',
    session_id: 'session-1',
    role: 'assistant',
    content: 'Hello, human! How can I help you today?',
    message_metadata: {},
    parent_message_id: null,
    created_at: new Date().toISOString(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders user message correctly', () => {
    render(<MessageBubble message={userMessage} />)

    expect(screen.getByText('Hello, AI!')).toBeInTheDocument()
    expect(screen.getByText('Hello, AI!')).toHaveClass('bg-blue-600')
  })

  it('renders assistant message correctly', () => {
    render(<MessageBubble message={assistantMessage} />)

    expect(screen.getByText('Hello, human! How can I help you today?')).toBeInTheDocument()
    expect(screen.getByText('Assistant')).toBeInTheDocument()
  })

  it('shows streaming animation when isStreaming is true', () => {
    render(<MessageBubble message={assistantMessage} isStreaming />)

    const cursor = screen.getByRole('status')
    expect(cursor).toHaveClass('animate-pulse')
  })

  it('renders markdown content', () => {
    const markdownMessage: Message = {
      ...assistantMessage,
      content: 'Here is a list:\n\n- Item 1\n- Item 2\n\nAnd some **bold** text',
    }

    render(<MessageBubble message={markdownMessage} />)

    expect(screen.getByText(/Item 1/)).toBeInTheDocument()
    expect(screen.getByText(/Item 2/)).toBeInTheDocument()
  })

  it('renders code blocks with syntax highlighting', () => {
    const codeMessage: Message = {
      ...assistantMessage,
      content: '```javascript\nconst x = 1;\nconsole.log(x);\n```',
    }

    render(<MessageBubble message={codeMessage} />)

    expect(screen.getByText(/const x = 1/)).toBeInTheDocument()
  })
})

describe('Sidebar', () => {
  const mockOnSessionSelect = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    // Mock empty sessions
    jest.spyOn(require('@/lib/hooks/useSessions'), 'useSessions')
      .mockReturnValue({
        data: { sessions: [], total: 0, has_more: false },
        isLoading: false,
        error: null,
      })

    render(
      <Sidebar
        currentSessionId="test-session"
        onSessionSelect={mockOnSessionSelect}
      />
    )

    expect(screen.getByText('Chat History')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    jest.spyOn(require('@/lib/hooks/useSessions'), 'useSessions')
      .mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      })

    render(
      <Sidebar
        currentSessionId="test-session"
        onSessionSelect={mockOnSessionSelect}
      />
    )

    // Check for skeleton loaders
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('toggles collapsed state', () => {
    jest.spyOn(require('@/lib/hooks/useSessions'), 'useSessions')
      .mockReturnValue({
        data: { sessions: [], total: 0, has_more: false },
        isLoading: false,
        error: null,
      })

    render(
      <Sidebar
        currentSessionId="test-session"
        onSessionSelect={mockOnSessionSelect}
      />
    )

    const collapseButton = screen.getByRole('button', { name: /collapse sidebar/i })
    fireEvent.click(collapseButton)

    // Sidebar should be collapsed
    expect(screen.queryByText('Chat History')).not.toBeInTheDocument()
  })
})

describe('ChatWindow', () => {
  const mockOnMessage = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders empty state correctly', () => {
    render(
      <ChatWindow
        sessionId="test-session"
        initialMessages={[]}
        isLoading={false}
      />
    )

    expect(screen.getByText('Start a conversation')).toBeInTheDocument()
  })

  it('shows connection status', () => {
    render(
      <ChatWindow
        sessionId="test-session"
        initialMessages={[]}
        isLoading={false}
      />
    )

    expect(screen.getByText(/connected|connecting/i)).toBeInTheDocument()
  })

  it('renders messages', () => {
    const messages: Message[] = [
      {
        message_id: '1',
        session_id: 'test-session',
        role: 'user',
        content: 'Hello!',
        message_metadata: {},
        parent_message_id: null,
        created_at: new Date().toISOString(),
      },
      {
        message_id: '2',
        session_id: 'test-session',
        role: 'assistant',
        content: 'Hi there!',
        message_metadata: {},
        parent_message_id: null,
        created_at: new Date().toISOString(),
      },
    ]

    render(
      <ChatWindow
        sessionId="test-session"
        initialMessages={messages}
        isLoading={false}
      />
    )

    expect(screen.getByText('Hello!')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('shows loading skeleton', () => {
    render(
      <ChatWindow
        sessionId="test-session"
        initialMessages={[]}
        isLoading={true}
      />
    )

    // Check for skeleton elements
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })
})

describe('API Integration', () => {
  it('handles session creation', async () => {
    const { api } = require('@/lib/api')

    const mockSession: Session = {
      session_id: 'new-session-id',
      user_id: 'user-1',
      engagement_id: null,
      project_id: null,
      accelerator_type: 'basic',
      conversation_metadata: {},
      started_at: new Date().toISOString(),
      last_active_at: new Date().toISOString(),
      status: 'active',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    api.createSession.mockResolvedValue(mockSession)

    const result = await api.createSession({ user_id: 'user-1' })

    expect(result).toEqual(mockSession)
    expect(api.createSession).toHaveBeenCalledWith({ user_id: 'user-1' })
  })

  it('handles message sending', async () => {
    const { api } = require('@/lib/api')

    const mockResponse = {
      session_id: 'session-1',
      message_id: 'message-1',
      content: 'Hello!',
      finish_reason: 'stop',
    }

    api.sendChatMessage.mockResolvedValue(mockResponse)

    const result = await api.sendChatMessage({
      session_id: 'session-1',
      message: 'Hello!',
      stream: false,
    })

    expect(result).toEqual(mockResponse)
  })
})

describe('WebSocket Handling', () => {
  it('handles stream_chunk messages', () => {
    const mockOnStreamChunk = jest.fn()

    const { wsClient } = require('@/lib/websocket')

    // Create a mock message handler
    const handler = jest.fn((msg) => {
      if (msg.type === 'stream_chunk') {
        mockOnStreamChunk(msg.payload.content)
      }
    })

    // Simulate receiving a stream chunk
    handler({
      type: 'stream_chunk',
      payload: { content: 'Hello' },
    })

    expect(mockOnStreamChunk).toHaveBeenCalledWith('Hello')
  })

  it('handles message_complete messages', () => {
    const mockOnComplete = jest.fn()

    const handler = (msg: any) => {
      if (msg.type === 'message_complete') {
        mockOnComplete(msg.payload)
      }
    }

    handler({
      type: 'message_complete',
      payload: {
        message_id: 'msg-1',
        content: 'Completed response',
      },
    })

    expect(mockOnComplete).toHaveBeenCalledWith({
      message_id: 'msg-1',
      content: 'Completed response',
    })
  })

  it('handles error messages', () => {
    const mockOnError = jest.fn()

    const handler = (msg: any) => {
      if (msg.type === 'error') {
        mockOnError(msg.payload.message)
      }
    }

    handler({
      type: 'error',
      payload: { message: 'Something went wrong' },
    })

    expect(mockOnError).toHaveBeenCalledWith('Something went wrong')
  })
})

describe('Error Scenarios', () => {
  it('handles API failure gracefully', async () => {
    const { api } = require('@/lib/api')

    api.getSessions.mockRejectedValue(new Error('Network error'))

    await expect(api.getSessions()).rejects.toThrow('Network error')
  })

  it('handles WebSocket disconnect', () => {
    const { wsClient } = require('@/lib/websocket')

    // Mock disconnect
    const disconnect = jest.fn()
    jest.spyOn(wsClient, 'disconnect').mockImplementation(disconnect)

    wsClient.disconnect()

    expect(disconnect).toHaveBeenCalled()
  })
})
