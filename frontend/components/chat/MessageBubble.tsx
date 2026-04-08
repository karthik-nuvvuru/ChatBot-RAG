'use client'

import { useState, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react'
import { cn, formatTime, copyToClipboard } from '@/lib/utils'
import type { Message } from '@/types/api'

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
  onRetry?: () => void
}

export function MessageBubble({ message, isStreaming, onRetry }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)

  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  const handleCopy = async () => {
    try {
      await copyToClipboard(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const codeBlocks = useMemo(() => {
    if (!isAssistant) return null

    const parts: React.ReactNode[] = []
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
    let lastIndex = 0
    let match
    let key = 0

    const text = message.content

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        const textPart = text.slice(lastIndex, match.index)
        parts.push(
          <div key={key++} className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {textPart}
            </ReactMarkdown>
          </div>
        )
      }

      // Add code block with syntax highlighting
      const language = match[1] || 'plaintext'
      const code = match[2].trim()

      parts.push(
        <div key={key++} className="relative group rounded-lg overflow-hidden my-2">
          <div className="absolute top-2 right-2 z-10">
            <button
              onClick={handleCopy}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-400" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>
          <SyntaxHighlighter
            language={language}
            className="!bg-gray-800 !text-gray-100 text-sm rounded-lg"
          >
            {code}
          </SyntaxHighlighter>
        </div>
      )

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textPart = text.slice(lastIndex)
      parts.push(
        <div key={key++} className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {textPart}
          </ReactMarkdown>
        </div>
      )
    }

    return parts.length > 0 ? parts : null
  }, [message.content, isAssistant, copied, handleCopy])

  return (
    <div
      className={cn(
        "flex animate-fade-in",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-800 text-gray-100",
          isStreaming && "animate-pulse-glow"
        )}
      >
        {/* Avatar and name for assistant */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold">
              AI
            </div>
            <span className="text-sm font-medium text-gray-400">Assistant</span>
          </div>
        )}

        {/* Message content */}
        <div className="prose prose-invert prose-sm max-w-none">
          {codeBlocks || (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Streaming cursor */}
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-blue-400 animate-pulse ml-1" />
        )}

        {/* Footer with time and actions */}
        <div className={cn(
          "flex items-center justify-between mt-2 pt-2 border-t border-opacity-20",
          isUser ? "border-white/20 justify-end" : "border-gray-700"
        )}>
          <span className={cn(
            "text-xs",
            isUser ? "text-white/70" : "text-gray-500"
          )}>
            {formatTime(message.created_at)}
          </span>

          {/* Feedback buttons for assistant */}
          {isAssistant && !isStreaming && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setShowFeedback(!showFeedback)}
                className="p-1 hover:bg-gray-700 rounded transition-colors"
              >
                <ThumbsUp className="w-4 h-4 text-gray-500 hover:text-green-400" />
              </button>
              <button
                onClick={onRetry}
                className="px-2 py-1 text-xs hover:bg-gray-700 rounded transition-colors"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MessageBubble
