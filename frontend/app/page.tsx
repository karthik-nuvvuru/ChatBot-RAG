'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()

  // Redirect to a new chat session
  useEffect(() => {
    // For now, just show the landing page
    // In a real app, this would redirect to /chat or show the landing
  }, [])

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <div className="w-72 border-r border-gray-800">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-gray-800">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              NelloreRuchullu
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Conversation AI Platform
            </p>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <button
              onClick={() => router.push('/chat/new')}
              className="flex items-center justify-center gap-2 w-full p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors font-medium"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-5 h-5"
              >
                <path d="M12 5v14M5 12h14" />
              </svg>
              New Chat
            </button>
          </div>

          {/* Recent Chats - Placeholder */}
          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Recent Chats
            </h2>
            <div className="text-center py-8 text-gray-500">
              <p className="text-sm">No recent chats</p>
              <p className="text-xs mt-1">Start a new conversation</p>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-800">
            <div className="flex items-center gap-3 text-sm text-gray-400">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold">
                U
              </div>
              <div className="flex-1 min-w-0">
                <p className="truncate">User</p>
                <p className="text-xs text-gray-600 truncate">user@example.com</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="text-center max-w-2xl">
          {/* Logo Animation */}
          <div className="relative mb-8">
            <div className="w-24 h-24 mx-auto rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/25">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-12 h-12 text-white"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="10" r="1" fill="currentColor" />
                <circle cx="8" cy="10" r="1" fill="currentColor" />
                <circle cx="16" cy="10" r="1" fill="currentColor" />
              </svg>
            </div>
            <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-white rounded-full animate-pulse" />
            </div>
          </div>

          <h1 className="text-4xl font-bold text-white mb-4">
            Welcome to{' '}
            <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              NelloreRuchullu
            </span>
          </h1>

          <p className="text-lg text-gray-400 mb-8">
            Your intelligent conversational AI assistant with memory, vector
            search, and real-time streaming capabilities.
          </p>

          {/* Feature Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
            <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
              <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="w-5 h-5 text-blue-400"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <h3 className="font-semibold text-white mb-1">Conversational AI</h3>
              <p className="text-sm text-gray-500">
                Natural language understanding and intelligent responses
              </p>
            </div>

            <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
              <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="w-5 h-5 text-purple-400"
                >
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
              </div>
              <h3 className="font-semibold text-white mb-1">Vector Search</h3>
              <p className="text-sm text-gray-500">
                Semantic search across all your conversations
              </p>
            </div>

            <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
              <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-green-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="w-5 h-5 text-green-400"
                >
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <h3 className="font-semibold text-white mb-1">Real-time Streaming</h3>
              <p className="text-sm text-gray-500">
                Instant responses with live streaming updates
              </p>
            </div>
          </div>

          {/* CTA */}
          <button
            onClick={() => router.push('/chat/new')}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors font-medium text-lg inline-flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="w-5 h-5"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
            Start New Chat
          </button>

          <p className="mt-4 text-sm text-gray-600">
            Free to use. No account required for demo.
          </p>
        </div>
      </div>
    </div>
  )
}
