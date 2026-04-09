'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, LogOut, MessageSquare, Sparkles, Search, Zap } from 'lucide-react'
import { getStoredUserId, getStoredToken } from '@/lib/hooks/useAuth'

export const dynamic = 'force-dynamic'

export default function HomePage() {
  const router = useRouter()
  const [userId, setUserId] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = getStoredToken()
    const stored = getStoredUserId()

    if (!token) {
      router.push('/login')
      return
    }

    setUserId(stored)
    setIsLoading(false)
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user_id')
    router.push('/login')
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center" style={{ backgroundColor: 'var(--background)' }}>
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--primary)' }} />
      </div>
    )
  }

  return (
    <div className="flex h-screen" style={{ backgroundColor: 'var(--background)' }}>
      {/* Sidebar */}
      <div className="w-72 border-r flex flex-col" style={{ backgroundColor: 'var(--background-alt)', borderColor: 'var(--border)' }}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b" style={{ borderColor: 'var(--border)' }}>
            <h1 className="text-xl font-bold" style={{ color: 'var(--primary)' }}>
              RAG Chatbot
            </h1>
            <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
              Conversational AI Platform
            </p>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <button
              onClick={() => router.push('/chat/new')}
              className="flex items-center justify-center gap-2 w-full py-3 text-white rounded-xl transition-all font-medium"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                <path d="M12 5v14M5 12h14" />
              </svg>
              New Chat
            </button>
          </div>

          {/* Recent Chats - Placeholder */}
          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--muted)' }}>
              Recent Chats
            </h2>
            <div className="text-center py-8" style={{ color: 'var(--muted)' }}>
              <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No recent chats</p>
              <p className="text-xs mt-1">Start a new conversation</p>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--foreground)' }}>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{ backgroundColor: 'var(--primary)' }}>
                {userId.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="truncate">{userId}</p>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>Logged in</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg transition-colors"
                style={{ color: 'var(--muted)' }}
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="text-center max-w-2xl">
          {/* Logo */}
          <div className="relative mb-8">
            <div
              className="w-24 h-24 mx-auto rounded-2xl flex items-center justify-center shadow-lg"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" className="w-12 h-12">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="10" r="1" fill="white" />
                <circle cx="8" cy="10" r="1" fill="white" />
                <circle cx="16" cy="10" r="1" fill="white" />
              </svg>
            </div>
          </div>

          <h1 className="text-4xl font-bold mb-4" style={{ color: 'var(--foreground)' }}>
            Welcome to <span style={{ color: 'var(--primary)' }}>RAG Chatbot</span>
          </h1>

          <p className="text-lg mb-8" style={{ color: 'var(--muted)' }}>
            Your intelligent conversational AI assistant with memory, vector search, and real-time streaming capabilities.
          </p>

          {/* Feature Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
            <div className="p-5 rounded-xl border card-hover" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="w-10 h-10 mx-auto mb-3 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--accent)' }}>
                <MessageSquare className="w-5 h-5 text-white" />
              </div>
              <h3 className="font-semibold mb-1" style={{ color: 'var(--foreground)' }}>Conversational AI</h3>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Natural language understanding and intelligent responses
              </p>
            </div>

            <div className="p-5 rounded-xl border card-hover" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="w-10 h-10 mx-auto mb-3 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--accent)' }}>
                <Search className="w-5 h-5 text-white" />
              </div>
              <h3 className="font-semibold mb-1" style={{ color: 'var(--foreground)' }}>Vector Search</h3>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Semantic search across all your conversations
              </p>
            </div>

            <div className="p-5 rounded-xl border card-hover" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="w-10 h-10 mx-auto mb-3 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--accent)' }}>
                <Zap className="w-5 h-5 text-white" />
              </div>
              <h3 className="font-semibold mb-1" style={{ color: 'var(--foreground)' }}>Real-time Streaming</h3>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Instant responses with live streaming updates
              </p>
            </div>
          </div>

          {/* CTA */}
          <button
            onClick={() => router.push('/chat/new')}
            className="px-8 py-4 text-white rounded-xl transition-all font-medium text-lg inline-flex items-center gap-2"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Start New Chat
          </button>

          <p className="mt-4 text-sm" style={{ color: 'var(--muted)' }}>
            Free to use. No account required for demo.
          </p>
        </div>
      </div>
    </div>
  )
}