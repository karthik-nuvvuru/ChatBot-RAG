'use client'

import { useEffect, useRef, useState, useCallback, memo, useMemo } from 'react'
import { MoreHorizontal, Download, Share2, ChevronDown, Bot, Zap } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { useChat } from '@/lib/hooks/useChat'
import type { Message } from '@/types/api'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'

interface ChatWindowProps {
  sessionId: string
  initialMessages?: Message[]
  isLoading?: boolean
}

// Suggestion chips for empty state
const SUGGESTIONS = [
  { icon: "💡", text: "Explain AI in simple terms", prompt: "Explain what artificial intelligence is in simple terms" },
  { icon: "💻", text: "Write Python code", prompt: "Write a Python function to calculate fibonacci numbers" },
  { icon: "📝", text: "Summarize text", prompt: "Summarize the key points of a long article" },
  { icon: "🔍", text: "Search the web", prompt: "What are the latest developments in AI?" },
]

// Typing indicator component
const TypingIndicator = memo(function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 animate-fade-in">
      <div className="avatar avatar-ai">
        <Bot className="w-4 h-4" />
      </div>
      <div className="message-assistant">
        <div className="typing-indicator">
          <span className="typing-dot" style={{ backgroundColor: 'var(--muted)' }} />
          <span className="typing-dot" style={{ backgroundColor: 'var(--muted)' }} />
          <span className="typing-dot" style={{ backgroundColor: 'var(--muted)' }} />
        </div>
      </div>
    </div>
  )
})

export const ChatWindow = memo(function ChatWindow({ sessionId, initialMessages, isLoading }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const [showHeaderMenu, setShowHeaderMenu] = useState(false)
  const [showScrollButton, setShowScrollButton] = useState(false)

  // Use state for messages to ensure proper re-renders
  const [messages, setMessages] = useState<Message[]>(initialMessages || [])

  // Streaming state
  const [streamingContent, setStreamingContent] = useState('')

  const queryClient = useQueryClient()

  // Initialize messages from props
  useEffect(() => {
    setMessages(initialMessages || [])
  }, [initialMessages])

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior })
  }, [])

  const handleScroll = useCallback(() => {
    if (!messagesContainerRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight

    setShowScrollButton(distanceFromBottom > 200)
  }, [])

  // Auto-scroll when new messages arrive
  useEffect(() => {
    scrollToBottom('smooth')
  }, [messages.length, scrollToBottom])

  const handleMessageReceived = useCallback((message: Message) => {
    setMessages(prev => {
      const existingIndex = prev.findIndex(m => m.message_id === message.message_id)

      if (existingIndex >= 0) {
        return prev.map((m, i) =>
          i === existingIndex ? message : m
        )
      }
      return [...prev, message]
    })
    scrollToBottom('smooth')
  }, [scrollToBottom])

  const handleStreamChunk = useCallback((chunk: string) => {
    setStreamingContent(prev => prev + chunk)
  }, [])

  const handleTypingIndicator = useCallback((userId: string, isTyping: boolean) => {
    // Could show typing indicator in UI
  }, [])

  const handleError = useCallback((error: string) => {
    console.error('Chat error:', error)
    // Show toast notification
  }, [])

  const {
    sendMessage,
    sendTypingStart,
    sendTypingStop,
    isConnected,
    isSending,
    streamingContent: wsStreamingContent,
  } = useChat({
    sessionId,
    onMessageReceived: handleMessageReceived,
    onStreamChunk: handleStreamChunk,
    onTypingIndicator: handleTypingIndicator,
    onError: handleError,
  })

  const handleSend = useCallback((message: string, attachments?: File[]) => {
    if (!message.trim()) return
    sendMessage(message, attachments)
  }, [sendMessage])

  const handleSuggestionClick = useCallback((prompt: string) => {
    handleSend(prompt)
  }, [handleSend])

  const exportChat = useCallback(() => {
    const content = messages
      .map(m => `${m.role.toUpperCase()}: ${m.content}`)
      .join('\n\n')

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-${sessionId}.txt`
    a.click()
    URL.revokeObjectURL(url)
    setShowHeaderMenu(false)
  }, [sessionId, messages])

  const isStreaming = wsStreamingContent.length > 0 || streamingContent.length > 0

  // Empty state
  const showEmptyState = messages.length === 0 && !isStreaming && !isSending

  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: 'var(--background)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-6 py-4 border-b"
        style={{ borderColor: 'var(--border)', backgroundColor: 'var(--background)' }}
      >
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--foreground)' }}>
            New Chat
          </h2>
          <div className="connection-indicator" style={{ color: isConnected ? 'var(--muted)' : 'var(--muted-foreground)' }}>
            <span className={cn("status-dot", isConnected ? "online" : "offline")} />
            <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowHeaderMenu(!showHeaderMenu)}
            className="p-2 rounded-xl hover:bg-white/5 transition-colors"
            style={{ color: 'var(--muted)' }}
          >
            <MoreHorizontal className="w-5 h-5" />
          </button>

          {showHeaderMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowHeaderMenu(false)} />
              <div
                className="absolute right-0 top-full mt-2 z-20 rounded-xl shadow-2xl py-2 min-w-48 border animate-fade-in"
                style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}
              >
                <button
                  onClick={exportChat}
                  className="flex items-center gap-3 w-full px-4 py-2.5 text-sm transition-colors hover:bg-white/5"
                  style={{ color: 'var(--foreground)' }}
                >
                  <Download className="w-4 h-4" />
                  Export chat
                </button>
                <button
                  className="flex items-center gap-3 w-full px-4 py-2.5 text-sm transition-colors hover:bg-white/5"
                  style={{ color: 'var(--foreground)' }}
                >
                  <Share2 className="w-4 h-4" />
                  Share
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-6"
      >
        {isLoading ? (
          <div className="space-y-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="flex items-start gap-3 animate-fade-in">
                <div className="w-8 h-8 rounded-full skeleton" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded skeleton" />
                  <div className="h-4 w-1/2 rounded skeleton" />
                </div>
              </div>
            ))}
          </div>
        ) : showEmptyState ? (
          /* Empty State with Suggestions */
          <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
            <div className="empty-state-icon">
              <Bot className="w-10 h-10 text-white" />
            </div>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--foreground)' }}>
              Start a conversation
            </h3>
            <p className="text-sm mb-8 max-w-md" style={{ color: 'var(--muted)' }}>
              Ask me anything and I&apos;ll do my best to help you. Here are some examples to get started:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-xl w-full">
              {SUGGESTIONS.map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestionClick(suggestion.prompt)}
                  className="suggestion-chip text-left animate-fade-in-up"
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <span className="text-lg">{suggestion.icon}</span>
                  <span style={{ color: 'var(--foreground)' }}>{suggestion.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(message => (
              <MessageBubble
                key={message.message_id}
                message={message}
              />
            ))}

            {/* Streaming message */}
            {isStreaming && (
              <MessageBubble
                key="streaming-message"
                message={{
                  message_id: 'streaming',
                  session_id: sessionId,
                  role: 'assistant',
                  content: wsStreamingContent || streamingContent,
                  message_metadata: {},
                  parent_message_id: null,
                  created_at: new Date().toISOString(),
                }}
                isStreaming
              />
            )}

            {/* Typing indicator */}
            {isSending && !isStreaming && <TypingIndicator />}
          </>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <button
          onClick={() => scrollToBottom('smooth')}
          className="absolute bottom-32 right-6 p-3 rounded-full shadow-lg border transition-all duration-200 hover:scale-105 animate-fade-in"
          style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}
        >
          <ChevronDown className="w-5 h-5" style={{ color: 'var(--muted)' }} />
        </button>
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onTypingStart={sendTypingStart}
        onTypingStop={sendTypingStop}
        disabled={false}
        placeholder="Ask anything..."
        isSending={isSending}
      />
    </div>
  )
})

export default ChatWindow