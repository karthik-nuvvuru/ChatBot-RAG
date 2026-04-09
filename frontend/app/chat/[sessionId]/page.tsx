'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Sidebar } from '@/components/sidebar/Sidebar'
import { ChatWindow } from '@/components/chat/ChatWindow'
import { useSession, useCreateSession } from '@/lib/hooks/useSessions'
import { useFlatMessages } from '@/lib/hooks/useMessages'
import { Loader2 } from 'lucide-react'
import { getStoredToken, getStoredUserId } from '@/lib/hooks/useAuth'
import type { Message } from '@/types/api'

// Force dynamic rendering - this page depends on auth tokens and WebSocket connections
export const dynamic = 'force-dynamic'

export default function ChatPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.sessionId as string

  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId)
  const [localMessages, setLocalMessages] = useState<Message[]>([])
  const [isAuthChecked, setIsAuthChecked] = useState(false)
  const initRef = useRef(false)

  const createSession = useCreateSession()
  const currentUserId = getStoredUserId()

  // Check auth on mount
  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      router.push('/login')
      return
    }
    setIsAuthChecked(true)
  }, [router])

  // Create a new session if we're on /chat/new
  useEffect(() => {
    if (!isAuthChecked) return
    if (initRef.current) return
    initRef.current = true

    const initSession = async () => {
      if (sessionId === 'new') {
        try {
          const newSession = await createSession.mutateAsync({
            user_id: currentUserId,
          })
          setCurrentSessionId(newSession.session_id)
          router.replace(`/chat/${newSession.session_id}`)
        } catch (error) {
          console.error('Failed to create session:', error)
          initRef.current = false // Reset for retry
          router.push('/')
        }
      } else {
        setCurrentSessionId(sessionId)
      }
    }

    initSession()
  }, [sessionId, createSession, router, isAuthChecked, currentUserId])

  // Fetch session data
  const { data: session, isLoading: isLoadingSession } = useSession(currentSessionId || '')

  // Fetch messages
  const {
    messages,
    isLoading: isLoadingMessages,
    fetchNextPage,
    hasNextPage,
  } = useFlatMessages(currentSessionId || '')

  // Combine fetched messages with local messages
  const allMessages = [...localMessages, ...messages]

  // Handle session selection
  const handleSessionSelect = (newSessionId: string) => {
    if (newSessionId !== currentSessionId) {
      setLocalMessages([])
      setCurrentSessionId(newSessionId)
    }
  }

  // Handle scroll for pagination
  const handleScroll = () => {
    if (hasNextPage && !isLoadingMessages) {
      fetchNextPage()
    }
  }

  // Show loading state
  if (sessionId === 'new' && createSession.isPending) {
    return (
      <div className="flex h-screen bg-gray-950 items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-400">Creating new chat...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (!sessionId || sessionId === 'new' && !createSession.isPending && !currentSessionId) {
    return (
      <div className="flex h-screen bg-gray-950 items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">Failed to load session</p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Go Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <Sidebar
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
      />

      {/* Chat Window */}
      <div className="flex-1">
        {currentSessionId && (
          <ChatWindow
            sessionId={currentSessionId}
            initialMessages={allMessages}
            isLoading={isLoadingSession || isLoadingMessages}
          />
        )}
      </div>
    </div>
  )
}
