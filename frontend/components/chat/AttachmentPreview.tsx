'use client'

import { useState } from 'react'
import { X, FileIcon, Image as ImageIcon, Loader2 } from 'lucide-react'
import { cn, formatFileSize, getFileExtension } from '@/lib/utils'

interface AttachmentPreviewProps {
  attachments: {
    id: string
    file: File
    preview?: string
    uploading?: boolean
    error?: string
    url?: string
  }[]
  onRemove: (id: string) => void
  maxPreviews?: number
}

export function AttachmentPreview({
  attachments,
  onRemove,
  maxPreviews = 4,
}: AttachmentPreviewProps) {
  if (attachments.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 p-3 bg-gray-800/50 rounded-lg">
      {attachments.slice(0, maxPreviews).map(attachment => (
        <div
          key={attachment.id}
          className={cn(
            "relative group flex items-center gap-2 bg-gray-800 rounded-lg p-2 pr-8",
            attachment.uploading && "opacity-60",
            attachment.error && "ring-1 ring-red-500"
          )}
        >
          {/* Preview */}
          {attachment.preview ? (
            <img
              src={attachment.preview}
              alt={attachment.file.name}
              className="w-12 h-12 object-cover rounded"
            />
          ) : (
            <div className="w-12 h-12 flex items-center justify-center bg-gray-700 rounded">
              {getFileExtension(attachment.file.name).toLowerCase() in ['jpg', 'jpeg', 'png', 'gif', 'webp'] ? (
                <ImageIcon className="w-6 h-6 text-gray-400" />
              ) : (
                <FileIcon className="w-6 h-6 text-gray-400" />
              )}
            </div>
          )}

          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm truncate">{attachment.file.name}</p>
            <p className="text-xs text-gray-500">
              {attachment.uploading ? (
                <span className="flex items-center gap-1 text-blue-400">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Uploading...
                </span>
              ) : attachment.error ? (
                <span className="text-red-400">{attachment.error}</span>
              ) : (
                formatFileSize(attachment.file.size)
              )}
            </p>
          </div>

          {/* Remove button */}
          <button
            onClick={() => onRemove(attachment.id)}
            className="absolute top-1 right-1 p-1 bg-gray-700 hover:bg-gray-600 rounded-full transition-colors"
          >
            <X className="w-3 h-3" />
          </button>

          {/* Upload progress ring */}
          {attachment.uploading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      ))}

      {/* Show count if more than max */}
      {attachments.length > maxPreviews && (
        <div className="w-12 h-12 flex items-center justify-center bg-gray-700 rounded-lg text-sm text-gray-400">
          +{attachments.length - maxPreviews}
        </div>
      )}
    </div>
  )
}

export default AttachmentPreview
