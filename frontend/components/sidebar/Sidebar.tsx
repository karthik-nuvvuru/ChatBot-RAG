'use client'

import { useState, memo, useMemo } from 'react'
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
  Clock,
} from 'lucide-react'
import { cn, formatRelativeTime, getSessionDisplayName } from '@/lib/utils'
import { useSessions, useCreateSession, useDeleteSession } from '@/lib/hooks/useSessions'
import { getStoredUserId } from '@/lib/hooks/useAuth'
import type { Session } from '@/types/api'

interface SidebarProps {
  currentSessionId?: string
  onSessionSelect?: (sessionId: string) => void
}

export const Sidebar = memo(function Sidebar({ currentSessionId, onSessionSelect }: SidebarProps) {
  const router = useRouter()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null)

  const currentUserId = getStoredUserId()

  const { data: sessionsData, isLoading, error } = useSessions({
    user_id: currentUserId,
    limit: 100
  })
  const createSession = useCreateSession()
  const deleteSession = useDeleteSession()

  // Group sessions by time period
  const groupedSessions = useMemo(() => {
    if (!sessionsData?.sessions) return { today: [], yesterday: [], lastWeek: [], older: [] }

    const now = new Date()
    const today = sessionsData.sessions.filter(s => {
      const date = new Date(s.last_active_at)
      return date.toDateString() === now.toDateString()
    })
    const yesterday = sessionsData.sessions.filter(s => {
      const date = new Date(s.last_active_at)
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      return date.toDateString() === yesterday.toDateString()
    })
    const lastWeek = sessionsData.sessions.filter(s => {
      const date = new Date(s.last_active_at)
      const weekAgo = new Date(now)
      weekAgo.setDate(weekAgo.getDate() - 7)
      return date > weekAgo && date.toDateString() !== now.toDateString()
    })
    const older = sessionsData.sessions.filter(s => {
      const date = new Date(s.last_active_at)
      const weekAgo = new Date(now)
      weekAgo.setDate(weekAgo.getDate() - 7)
      return date <= weekAgo
    })

    return { today, yesterday, lastWeek, older }
  }, [sessionsData])

  const handleNewChat = async () => {
    try {
      const newSession = await createSession.mutateAsync({
        user_id: currentUserId,
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
        "flex flex-col h-full border-r",
        isCollapsed ? "w-16" : "w-72"
      )} style={{ backgroundColor: 'var(--background-alt)', borderColor: 'var(--border)' }}>
        <div className="p-4 text-sm" style={{ color: 'var(--error)' }}>
          Failed to load sessions
        </div>
      </div>
    )
  }

  return (
    <div className={cn(
      "flex flex-col h-full border-r transition-all duration-300",
      isCollapsed ? "w-16" : "w-72"
    )} style={{ backgroundColor: 'var(--background-alt)', borderColor: 'var(--border)' }}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'var(--border)' }}>
        {!isCollapsed && (
          <h1 className="text-lg font-semibold" style={{ color: 'var(--primary)' }}>
            RAG Chatbot
          </h1>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 rounded-lg transition-colors"
          style={{ color: 'var(--muted)' }}
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
            "flex items-center justify-center gap-2 w-full py-3 text-white rounded-xl transition-all font-medium",
            createSession.isPending && "opacity-50 cursor-not-allowed"
          )}
          style={{ backgroundColor: 'var(--primary)' }}
        >
          <Plus className="w-5 h-5" />
          {!isCollapsed && <span>{createSession.isPending ? 'Creating...' : 'New Chat'}</span>}
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-14 rounded-xl skeleton" style={{ backgroundColor: 'var(--card)' }} />
            ))}
          </div>
        ) : sessionsData?.sessions.length === 0 ? (
          !isCollapsed && (
            <div className="p-6 text-center">
              <MessageSquare className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--muted)', opacity: 0.5 }} />
              <p className="text-sm" style={{ color: 'var(--muted)' }}>No conversations yet</p>
              <p className="text-xs mt-1" style={{ color: 'var(--muted)', opacity: 0.7 }}>Start a new chat to begin</p>
            </div>
          )
        ) : (
          !isCollapsed && (
            <div className="p-2 space-y-4">
              {/* Today */}
              {groupedSessions.today.length > 0 && (
                <SessionGroup
                  title="Today"
                  sessions={groupedSessions.today}
                  currentSessionId={currentSessionId}
                  deletingSessionId={deletingSessionId}
                  onClick={handleSessionClick}
                  onDelete={handleDeleteSession}
                />
              )}

              {/* Yesterday */}
              {groupedSessions.yesterday.length > 0 && (
                <SessionGroup
                  title="Yesterday"
                  sessions={groupedSessions.yesterday}
                  currentSessionId={currentSessionId}
                  deletingSessionId={deletingSessionId}
                  onClick={handleSessionClick}
                  onDelete={handleDeleteSession}
                />
              )}

              {/* Last Week */}
              {groupedSessions.lastWeek.length > 0 && (
                <SessionGroup
                  title="Last Week"
                  sessions={groupedSessions.lastWeek}
                  currentSessionId={currentSessionId}
                  deletingSessionId={deletingSessionId}
                  onClick={handleSessionClick}
                  onDelete={handleDeleteSession}
                />
              )}

              {/* Older */}
              {groupedSessions.older.length > 0 && (
                <SessionGroup
                  title="Older"
                  sessions={groupedSessions.older}
                  currentSessionId={currentSessionId}
                  deletingSessionId={deletingSessionId}
                  onClick={handleSessionClick}
                  onDelete={handleDeleteSession}
                />
              )}
            </div>
          )
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t space-y-1" style={{ borderColor: 'var(--border)' }}>
        <button
          className="flex items-center gap-3 w-full p-3 rounded-xl transition-colors"
          style={{ color: 'var(--muted)' }}
        >
          <Settings className="w-5 h-5" />
          {!isCollapsed && <span className="text-sm">Settings</span>}
        </button>
        <button
          className="flex items-center gap-3 w-full p-3 rounded-xl transition-colors"
          style={{ color: 'var(--muted)' }}
        >
          <LogOut className="w-5 h-5" />
          {!isCollapsed && <span className="text-sm">Log out</span>}
        </button>
      </div>
    </div>
  )
})

interface SessionGroupProps {
  title: string
  sessions: Session[]
  currentSessionId?: string
  deletingSessionId: string | null
  onClick: (session: Session) => void
  onDelete: (e: React.MouseEvent, sessionId: string) => void
}

const SessionGroup = memo(function SessionGroup({
  title,
  sessions,
  currentSessionId,
  deletingSessionId,
  onClick,
  onDelete,
}: SessionGroupProps) {
  return (
    <div>
      <div className="flex items-center gap-2 px-3 py-2">
        <Clock className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
        <span className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
          {title}
        </span>
      </div>
      <div className="space-y-1">
        {sessions.map(session => (
          <SessionItem
            key={session.session_id}
            session={session}
            isActive={currentSessionId === session.session_id}
            isDeleting={deletingSessionId === session.session_id}
            onClick={() => onClick(session)}
            onDelete={(e) => onDelete(e, session.session_id)}
          />
        ))}
      </div>
    </div>
  )
})

interface SessionItemProps {
  session: Session
  isActive: boolean
  isDeleting: boolean
  onClick: () => void
  onDelete: (e: React.MouseEvent) => void
}

const SessionItem = memo(function SessionItem({
  session,
  isActive,
  isDeleting,
  onClick,
  onDelete,
}: SessionItemProps) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div
      className={cn(
        "group relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200"
      )}
      style={{
        backgroundColor: isActive ? 'var(--card)' : 'transparent',
        borderWidth: '1px',
        borderColor: isActive ? 'var(--accent)' : 'transparent',
        opacity: isDeleting ? 0.5 : 1,
        pointerEvents: isDeleting ? 'none' : 'auto',
      }}
      onClick={onClick}
    >
      <MessageSquare className={cn(
        "w-5 h-5 flex-shrink-0 transition-colors"
      )} style={{ color: isActive ? 'var(--accent)' : 'var(--muted)' }} />

      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium" style={{ color: 'var(--foreground)' }}>
          {getSessionDisplayName(session)}
        </p>
        <p className="text-xs truncate" style={{ color: 'var(--muted)' }}>
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
          className="p-1.5 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
          style={{ color: 'var(--muted)' }}
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
            <div
              className="absolute right-0 bottom-full mb-1 z-20 rounded-xl shadow-lg py-1 min-w-36 border"
              style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}
            >
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowMenu(false)
                  onDelete(e)
                }}
                className="flex items-center gap-2 w-full px-4 py-2.5 text-sm transition-colors"
                style={{ color: 'var(--error)' }}
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
})

export default Sidebar