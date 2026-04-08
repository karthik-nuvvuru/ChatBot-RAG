'use client'

import { useState, useRef, useCallback, useEffect, KeyboardEvent, ChangeEvent } from 'react'
import {
  SendHorizontal,
  Paperclip,
  Minus,
  Square,
  Image,
  File,
  X,
} from 'lucide-react'
import { cn, formatFileSize } from '@/lib/utils'

interface Attachment {
  id: string
  file: File
  preview?: string
}

interface ChatInputProps {
  onSend: (message: string, attachments?: File[]) => void
  onTypingStart?: () => void
  onTypingStop?: () => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  onTypingStart,
  onTypingStop,
  disabled,
  placeholder = 'Type a message...',
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [message])

  // Handle typing indicator
  const handleTypingStart = useCallback(() => {
    if (!isTyping) {
      setIsTyping(true)
      onTypingStart?.()
    }
  }, [isTyping, onTypingStart])

  const handleTypingStop = useCallback(() => {
    if (isTyping) {
      setIsTyping(false)
      onTypingStop?.()
    }
  }, [isTyping, onTypingStop])

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)
    if (e.target.value.trim()) {
      handleTypingStart()
    } else {
      handleTypingStop()
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    const trimmedMessage = message.trim()
    if (!trimmedMessage && attachments.length === 0) return

    onSend(trimmedMessage, attachments.map(a => a.file))
    setMessage('')
    setAttachments([])
    handleTypingStop()

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    textareaRef.current?.focus()
  }

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const newAttachments: Attachment[] = Array.from(files).map(file => ({
      id: Math.random().toString(36).substring(2, 9),
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    }))

    setAttachments(prev => [...prev, ...newAttachments])

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeAttachment = (id: string) => {
    setAttachments(prev => {
      const removed = prev.find(a => a.id === id)
      if (removed?.preview) {
        URL.revokeObjectURL(removed.preview)
      }
      return prev.filter(a => a.id !== id)
    })
  }

  return (
    <div className="border-t border-gray-800 bg-gray-900 px-4 py-4">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {attachments.map(attachment => (
            <div
              key={attachment.id}
              className="relative group flex items-center gap-2 bg-gray-800 rounded-lg p-2 pr-8"
            >
              {attachment.preview ? (
                <Image
                  src={attachment.preview}
                  alt={attachment.file.name}
                  className="w-10 h-10 object-cover rounded"
                />
              ) : (
                <File className="w-10 h-10 text-gray-400" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate">{attachment.file.name}</p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(attachment.file.size)}
                </p>
              </div>
              <button
                onClick={() => removeAttachment(attachment.id)}
                className="absolute top-1 right-1 p-1 bg-gray-700 hover:bg-gray-600 rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-3">
        {/* Attachment Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className={cn(
            "p-3 rounded-xl transition-colors",
            disabled
              ? "bg-gray-800 text-gray-500 cursor-not-allowed"
              : "bg-gray-800 hover:bg-gray-700 text-gray-400"
          )}
        >
          <Paperclip className="w-5 h-5" />
        </button>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept="image/*,.pdf,.doc,.docx,.txt"
        />

        {/* Text Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onBlur={handleTypingStop}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              "w-full resize-none bg-gray-800 text-white rounded-xl px-4 py-3 pr-12",
              "placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "max-h-48 overflow-y-auto"
            )}
          />

          {/* Character count (shown when near limit) */}
          {message.length > 9000 && (
            <span className="absolute bottom-2 right-12 text-xs text-gray-500">
              {message.length}/10000
            </span>
          )}
        </div>

        {/* Send / Stop Button */}
        {disabled ? (
          <button
            onClick={() => {/* TODO: Implement stop */}}
            className="p-3 bg-red-600 hover:bg-red-700 rounded-xl transition-colors"
          >
            <Square className="w-5 h-5" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!message.trim() && attachments.length === 0}
            className={cn(
              "p-3 rounded-xl transition-colors",
              message.trim() || attachments.length > 0
                ? "bg-blue-600 hover:bg-blue-700 text-white"
                : "bg-gray-800 text-gray-500 cursor-not-allowed"
            )}
          >
            <SendHorizontal className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Hint */}
      <p className="mt-2 text-xs text-gray-600 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
}

export default ChatInput
