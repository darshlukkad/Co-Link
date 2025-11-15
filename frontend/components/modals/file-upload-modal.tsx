'use client'

import { FileUpload } from '@/components/chat/file-upload'

interface FileUploadModalProps {
  isOpen: boolean
  onClose: () => void
  workspaceId: string
  channelId?: string
  onUploadComplete?: (fileId: string) => void
}

export function FileUploadModal({
  isOpen,
  onClose,
  workspaceId,
  channelId,
  onUploadComplete,
}: FileUploadModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg">
        <FileUpload
          workspaceId={workspaceId}
          channelId={channelId}
          onUploadComplete={onUploadComplete}
          onClose={onClose}
        />
      </div>
    </div>
  )
}
