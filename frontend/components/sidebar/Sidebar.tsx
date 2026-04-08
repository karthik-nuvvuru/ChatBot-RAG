'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Plus,
  MessageSquare,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Trash2,
  MoreVertical,
} from 'lucide-react'
import { cn, formatRelativeTime, getSessionDisplayName } from '@/lib/utils'
import { useSessions, useCreateSession, useDeleteSession } from '@/lib/hooks/useSessions'
import type { Session } from '@/types/api'

interface SidebarProps {
  currentSessionId?: string
  onSessionSelect?: (sessionId: string) => void
}

export function Sidebar({ currentSessionId, onSessionSelect }: SidebarProps) {
  const router = useRouter()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null)

  const { data: sessionsData, isLoading, error } = useSessions({ limit: 50 })
  const createSession = useCreateSession()
  const deleteSession = useDeleteSession()

  const handleNewChat = async () => {
    try {
      const newSession = await createSession.mutateAsync({
        user_id: 'default-user', // In real app, get from auth
      })
      onSessionSelect?.(newSession.session_id)
      router.push(`/chat/${newSession.session_id}`)
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  }

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    setDeletingSessionId(sessionId)

    try {
      await deleteSession.mutateAsync(sessionId)
      if (currentSessionId === sessionId) {
        router.push('/')
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    } finally {
      setDeletingSessionId(null)
    }
  }

  const handleSessionClick = (session: Session) => {
    onSessionSelect?.(session.session_id)
    router.push(`/chat/${session.session_id}`)
  }

  if (error) {
    return (
      <div className={cn(
        "flex flex-col h-full bg-gray-900 text-white",
        isCollapsed ? "w-16" : "w-72"
      )}>
        <div className="p-4 text-red-400">
          Failed to load sessions
        </div>
      </div>
    )
  }

  return (
    <div className={cn(
      "flex flex-col h-full bg-gray-900 text-white transition-all duration-300",
      isCollapsed ? "w-16" : "w-72"
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        {!isCollapsed && (
          <h1 className="text-lg font-semibold truncate">Chat History</h1>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <ChevronLeft className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          disabled={createSession.isPending}
          className={cn(
            "flex items-center gap-3 w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors",
            createSession.isPending && "opacity-50 cursor-not-allowed"
          )}
        >
          <Plus className="w-5 h-5 flex-shrink-0" />
          {!isCollapsed && (
            <span className="truncate">
              {createSession.isPending ? 'Creating...' : 'New Chat'}
            </span>
          )}
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-gray-800 rounded-lg" />
              </div>
            ))}
          </div>
        ) : sessionsData?.sessions.length === 0 ? (
          !isCollapsed && (
            <div className="p-4 text-center text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations yet</p>
              <p className="text-xs mt-1">Start a new chat to begin</p>
            </div>
          )
        ) : (
          <div className="p-2 space-y-1">
            {sessionsData?.sessions.map(session => (
              <SessionItem
                key={session.session_id}
                session={session}
                isActive={currentSessionId === session.session_id}
                isCollapsed={isCollapsed}
                isDeleting={deletingSessionId === session.session_id}
                onClick={() => handleSessionClick(session)}
                onDelete={(e) => handleDeleteSession(e, session.session_id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-800 space-y-1">
        <button
          className={cn(
            "flex items-center gap-3 w-full p-3 hover:bg-gray-800 rounded-lg transition-colors text-gray-400"
          )}
        >
          <Settings className="w-5 h-5 flex-shrink-0" />
          {!isCollapsed && <span className="truncate">Settings</span>}
        </button>
        <button
          className={cn(
            "flex items-center gap-3 w-full p-3 hover:bg-gray-800 rounded-lg transition-colors text-gray-400"
          )}
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!isCollapsed && <span className="truncate">Log out</span>}
        </button>
      </div>
    </div>
  )
}

interface SessionItemProps {
  session: Session
  isActive: boolean
  isCollapsed: boolean
  isDeleting: boolean
  onClick: () => void
  onDelete: (e: React.MouseEvent) => void
}

function SessionItem({
  session,
  isActive,
  isCollapsed,
  isDeleting,
  onClick,
  onDelete,
}: SessionItemProps) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div
      className={cn(
        "group relative flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
        isActive
          ? "bg-gray-700"
          : "hover:bg-gray-800",
        isDeleting && "opacity-50 pointer-events-none"
      )}
      onClick={onClick}
    >
      <MessageSquare className="w-5 h-5 flex-shrink-0 text-gray-400" />

      {!isCollapsed && (
        <>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium">
              {getSessionDisplayName(session)}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {formatRelativeTime(session.last_active_at)}
            </p>
          </div>

          {/* Actions */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
              className="p-1 hover:bg-gray-600 rounded opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical className="w-4 h-4" />
            </button>

            {showMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowMenu(false)
                  }}
                />
                <div className="absolute right-0 bottom-full mb-1 z-20 bg-gray-800 rounded-lg shadow-lg py-1 min-w-32">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowMenu(false)
                      onDelete(e)
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400 hover:bg-gray-700"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default Sidebar
