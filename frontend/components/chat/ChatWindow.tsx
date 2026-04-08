'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { MoreHorizontal, Download, Share2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChat } from '@/lib/hooks/useChat'
import type { Message } from '@/types/api'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import TypingIndicator from './TypingIndicator'

interface ChatWindowProps {
  sessionId: string
  initialMessages?: Message[]
  isLoading?: boolean
}

export function ChatWindow({ sessionId, initialMessages, isLoading }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const [showHeaderMenu, setShowHeaderMenu] = useState(false)
  const [messages, setMessages] = useState<Message[]>(initialMessages || [])

  const queryClient = useQueryClient()

  // Update messages when initialMessages changes
  useEffect(() => {
    if (initialMessages) {
      setMessages(initialMessages)
    }
  }, [initialMessages])

  // Auto-scroll to bottom on new messages
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Handle new message from WebSocket
  const handleMessageReceived = useCallback((message: Message) => {
    setMessages(prev => {
      // Check if message already exists (for optimistic updates)
      const exists = prev.some(m => m.message_id === message.message_id)
      if (exists) {
        return prev.map(m => m.message_id === message.message_id ? message : m)
      }
      return [...prev, message]
    })
  }, [])

  // Handle streaming chunks
  const [streamingContent, setStreamingContent] = useState('')
  const [isAssistantTyping, setIsAssistantTyping] = useState(false)

  const handleStreamChunk = useCallback((chunk: string) => {
    setStreamingContent(prev => prev + chunk)
    setIsAssistantTyping(true)
  }, [])

  const handleTypingIndicator = useCallback((userId: string, isTyping: boolean) => {
    if (userId !== 'assistant') return
    setIsAssistantTyping(isTyping)
  }, [])

  const handleError = useCallback((error: string) => {
    console.error('Chat error:', error)
    setIsAssistantTyping(false)
  }, [])

  // Chat hook
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

  // Combine streaming content
  const displayStreamingContent = wsStreamingContent || streamingContent

  // Handle send message
  const handleSend = (message: string, attachments?: File[]) => {
    sendMessage(message, attachments)
  }

  // Export chat
  const exportChat = () => {
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
  }

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div>
          <h2 className="text-lg font-semibold text-white">New Chat</h2>
          <p className="text-sm text-gray-500">
            {isConnected ? (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full" />
                Connected
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full" />
                Connecting...
              </span>
            )}
          </p>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowHeaderMenu(!showHeaderMenu)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <MoreHorizontal className="w-5 h-5 text-gray-400" />
          </button>

          {showHeaderMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowHeaderMenu(false)}
              />
              <div className="absolute right-0 top-full mt-1 z-20 bg-gray-800 rounded-lg shadow-lg py-1 min-w-40">
                <button
                  onClick={exportChat}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm hover:bg-gray-700"
                >
                  <Download className="w-4 h-4" />
                  Export chat
                </button>
                <button
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm hover:bg-gray-700"
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
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
      >
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-800" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-800 rounded w-3/4" />
                    <div className="h-4 bg-gray-800 rounded w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : messages.length === 0 && !isAssistantTyping ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl font-bold mb-4">
              AI
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Start a conversation
            </h3>
            <p className="text-gray-500 max-w-md">
              Ask me anything and I&apos;ll do my best to help you.
            </p>
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
            {isAssistantTyping && displayStreamingContent && (
              <MessageBubble
                message={{
                  message_id: 'streaming',
                  session_id: sessionId,
                  role: 'assistant',
                  content: displayStreamingContent,
                  message_metadata: {},
                  parent_message_id: null,
                  created_at: new Date().toISOString(),
                }}
                isStreaming
              />
            )}

            {/* Typing indicator */}
            {isAssistantTyping && !displayStreamingContent && (
              <TypingIndicator />
            )}
          </>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onTypingStart={sendTypingStart}
        onTypingStop={sendTypingStop}
        disabled={!isConnected}
        placeholder={isConnected ? "Type a message..." : "Connecting..."}
      />
    </div>
  )
}

export default ChatWindow
