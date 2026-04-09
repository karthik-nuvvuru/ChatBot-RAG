'use client'

import { memo } from 'react'
import { ExternalLink, FileText, Globe, Bookmark } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Source {
  id: string
  title: string
  url?: string
  type: 'web' | 'document' | 'file'
  snippet?: string
  relevance?: number
}

interface RAGPanelProps {
  sources?: Source[]
  isLoading?: boolean
  className?: string
}

export const RAGPanel = memo(function RAGPanel({
  sources = [],
  isLoading = false,
  className,
}: RAGPanelProps) {
  // Demo sources for when no real data
  const demoSources: Source[] = [
    {
      id: '1',
      title: 'Introduction to RAG Systems',
      url: 'https://docs.example.com/rag-intro',
      type: 'web',
      snippet: 'Retrieval-Augmented Generation (RAG) is a technique for enhancing LLM accuracy...',
      relevance: 0.92,
    },
    {
      id: '2',
      title: 'Vector Database Best Practices',
      url: 'https://docs.example.com/vector-db',
      type: 'document',
      snippet: 'pgvector provides efficient vector similarity search capabilities...',
      relevance: 0.87,
    },
    {
      id: '3',
      title: 'Conversational AI Patterns',
      url: 'https://docs.example.com/ai-patterns',
      type: 'file',
      snippet: 'Best practices for building conversational AI systems with context retention...',
      relevance: 0.81,
    },
  ]

  const displaySources = sources.length > 0 ? sources : demoSources

  const getIcon = (type: Source['type']) => {
    switch (type) {
      case 'web':
        return <Globe className="w-4 h-4" />
      case 'document':
        return <FileText className="w-4 h-4" />
      case 'file':
        return <Bookmark className="w-4 h-4" />
      default:
        return <ExternalLink className="w-4 h-4" />
    }
  }

  return (
    <div
      className={cn(
        "h-full flex flex-col border-l",
        className
      )}
      style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}
    >
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: 'var(--border)' }}>
        <h2 className="font-semibold" style={{ color: 'var(--foreground)' }}>
          Sources & References
        </h2>
        <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
          Related documents and web sources
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <>
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 rounded-lg skeleton" style={{ backgroundColor: 'var(--background)' }} />
            ))}
          </>
        ) : displaySources.length === 0 ? (
          <div className="text-center py-8">
            <Bookmark className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--muted)', opacity: 0.5 }} />
            <p className="text-sm" style={{ color: 'var(--muted)' }}>No sources available</p>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)', opacity: 0.7 }}>
              Sources will appear when you ask questions
            </p>
          </div>
        ) : (
          displaySources.map(source => (
            <div
              key={source.id}
              className="rag-source group"
            >
              <div className="rag-source-icon">
                {getIcon(source.type)}
              </div>
              <div className="flex-1 min-w-0">
                <a
                  href={source.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rag-source-title hover:underline"
                  style={{ color: 'var(--foreground)' }}
                >
                  {source.title}
                </a>
                {source.snippet && (
                  <p className="text-xs mt-1 line-clamp-2" style={{ color: 'var(--muted)' }}>
                    {source.snippet}
                  </p>
                )}
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rag-source-link flex items-center gap-1 mt-1"
                  >
                    <ExternalLink className="w-3 h-3" />
                    {new URL(source.url).hostname}
                  </a>
                )}
              </div>
              {source.relevance && (
                <div
                  className="text-xs font-medium px-2 py-1 rounded-full"
                  style={{
                    backgroundColor: 'var(--accent)',
                    color: 'white',
                  }}
                >
                  {Math.round(source.relevance * 100)}%
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t text-center" style={{ borderColor: 'var(--border)' }}>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Powered by RAG retrieval
        </p>
      </div>
    </div>
  )
})

export default RAGPanel