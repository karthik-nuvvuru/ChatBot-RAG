'use client'

import { useState, useRef, useCallback, useEffect, KeyboardEvent, ChangeEvent, memo } from 'react'
import { SendHorizontal, Square } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string, attachments?: File[]) => void
  onTypingStart?: () => void
  onTypingStop?: () => void
  disabled?: boolean
  placeholder?: string
  isSending?: boolean
  onStop?: () => void
}

export const ChatInput = memo(function ChatInput({
  onSend,
  onTypingStart,
  onTypingStop,
  disabled,
  placeholder = "Ask anything...",
  isSending = false,
  onStop,
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [message])

  const handleSend = useCallback(() => {
    const trimmed = message.trim()
    if (!trimmed) return

    onSend(trimmed)
    setMessage('')

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    textareaRef.current?.focus()
  }, [message, onSend])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isSending && message.trim()) {
        handleSend()
      }
    }
  }

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)
  }

  const canSend = message.trim().length > 0

  return (
    <div
      className={cn(
        "border-t px-4 py-4 transition-all duration-300",
        isFocused && "bg-opacity-100"
      )}
      style={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)' }}
    >
      {/* Input Area */}
      <div
        className={cn(
          "flex items-end gap-3 px-4 py-3 rounded-2xl border transition-all duration-300"
        )}
        style={{
          backgroundColor: 'var(--card)',
          borderColor: isFocused ? 'var(--primary)' : 'var(--border)',
          boxShadow: isFocused ? '0 0 0 2px rgba(59, 130, 246, 0.2)' : '0 4px 16px rgba(0, 0, 0, 0.2)',
        }}
      >
        {/* Text Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            disabled={disabled || isSending}
            rows={1}
            className="chat-input"
            style={{ color: 'var(--foreground)' }}
          />
        </div>

        {/* Send / Stop Button */}
        <button
          onClick={isSending ? onStop : handleSend}
          disabled={!canSend || disabled}
          className={cn(
            "p-3 rounded-xl transition-all duration-200 flex-shrink-0",
            isSending
              ? "bg-red-500/80 hover:bg-red-500"
              : canSend && !disabled
                ? "gradient-bg hover:opacity-90 active:scale-95"
                : "opacity-50 cursor-not-allowed"
          )}
          style={!(isSending || (canSend && !disabled)) ? { backgroundColor: 'var(--card-hover)' } : {}}
        >
          {isSending ? (
            <Square className="w-5 h-5 text-white" />
          ) : (
            <SendHorizontal className="w-5 h-5 text-white" />
          )}
        </button>
      </div>

      {/* Hint */}
      <p className="mt-2 text-xs text-center" style={{ color: 'var(--muted-foreground)' }}>
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
})

export default ChatInput