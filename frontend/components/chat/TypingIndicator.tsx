'use client'

import { cn } from '@/lib/utils'

interface TypingIndicatorProps {
  className?: string
}

export function TypingIndicator({ className }: TypingIndicatorProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 px-4 py-3 bg-gray-800 rounded-2xl rounded-tl-sm w-fit",
        className
      )}
    >
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold">
        AI
      </div>

      {/* Dots */}
      <div className="flex items-center gap-1">
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '0ms' }}
        />
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '150ms' }}
        />
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '300ms' }}
        />
      </div>

      <span className="text-sm text-gray-400 ml-1">thinking...</span>
    </div>
  )
}

export default TypingIndicator
