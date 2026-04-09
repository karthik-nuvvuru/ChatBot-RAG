'use client'

import { useState, useMemo, memo, useCallback, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { Copy, Check, RotateCcw, User, Bot } from 'lucide-react'
import { cn, formatTime, copyToClipboard } from '@/lib/utils'
import type { Message } from '@/types/api'

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
  onRetry?: () => void
}

export const MessageBubble = memo(function MessageBubble({
  message,
  isStreaming,
  onRetry,
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = useCallback(async () => {
    try {
      await copyToClipboard(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }, [message.content])

  // Parse markdown content
  const renderContent = useCallback(() => {
    if (isStreaming) {
      return (
        <span className="text-sm leading-relaxed">
          {message.content}
          <span className="inline-block w-0.5 h-4 bg-primary ml-1 animate-cursor rounded-full" />
        </span>
      )
    }

    return (
      <div className="prose-dark">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {message.content}
        </ReactMarkdown>
      </div>
    )
  }, [message.content, isStreaming])

  return (
    <div
      className={cn(
        "flex w-full animate-fade-in-up",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] flex gap-3",
          isUser ? "flex-row-reverse" : "flex-row"
        )}
      >
        {/* Avatar */}
        <div
          className={cn(
            "avatar flex-shrink-0",
            isUser ? "avatar-user" : "avatar-ai"
          )}
        >
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>

        {/* Message bubble */}
        <div
          className={cn(
            "relative group",
            isUser ? "items-end" : "items-start"
          )}
        >
          <div
            className={cn(
              isUser ? "message-user" : "message-assistant"
            )}
          >
            {renderContent()}
          </div>

          {/* Actions bar (show on hover) */}
          {!isStreaming && (
            <div
              className={cn(
                "absolute -top-2 flex items-center gap-1 px-2 py-1 rounded-lg border transition-all duration-200",
                "opacity-0 group-hover:opacity-100",
                isUser ? "right-0" : "left-0"
              )}
              style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}
            >
              <button
                onClick={handleCopy}
                className="p-1.5 rounded hover:bg-white/10 transition-colors"
                title="Copy message"
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-green-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                )}
              </button>
              {onRetry && !isUser && (
                <button
                  onClick={onRetry}
                  className="p-1.5 rounded hover:bg-white/10 transition-colors"
                  title="Regenerate response"
                >
                  <RotateCcw className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                </button>
              )}
            </div>
          )}

          {/* Timestamp */}
          <div
            className={cn(
              "text-xs mt-1 px-1",
              isUser ? "text-right" : "text-left"
            )}
            style={{ color: 'var(--muted-foreground)' }}
          >
            {formatTime(message.created_at)}
          </div>
        </div>
      </div>
    </div>
  )
}, (prevProps, nextProps) => {
  // Only re-render if content changes or streaming state changes
  if (prevProps.message.message_id !== nextProps.message.message_id) return false
  if (prevProps.isStreaming !== nextProps.isStreaming) return true
  if (prevProps.message.content !== nextProps.message.content) return true
  return false
})

export default MessageBubble