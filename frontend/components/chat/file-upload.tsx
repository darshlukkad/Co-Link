'use client'

import { useState, useRef } from 'react'
import { Upload, X, File, Image as ImageIcon, FileText, Video } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  workspaceId: string
  channelId?: string
  onUploadComplete?: (fileId: string) => void
  onClose?: () => void
}

export function FileUpload({ workspaceId, channelId, onUploadComplete, onClose }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }

  const handleFileSelect = (selectedFile: File) => {
    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024
    if (selectedFile.size > maxSize) {
      setError('File size exceeds 100MB limit')
      return
    }

    setFile(selectedFile)
    setError(null)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSelect(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setError(null)

    try {
      // Get presigned upload URL
      // @ts-expect-error - getUploadUrl method needs to be added to ApiClient type definition
      const { file_id, upload_url, expires_at } = await apiClient.getUploadUrl(
        file.name,
        file.type,
        file.size,
        workspaceId
      )

      // Upload directly to S3 using presigned URL
      const uploadResponse = await fetch(upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      })

      if (!uploadResponse.ok) {
        throw new Error('Upload failed')
      }

      // Confirm upload
      // @ts-expect-error - confirmUpload method needs to be added to ApiClient type definition
      await apiClient.confirmUpload(file_id)

      setUploadProgress(100)

      if (onUploadComplete) {
        onUploadComplete(file_id)
      }

      // Reset
      setTimeout(() => {
        setFile(null)
        setUploadProgress(0)
        if (onClose) onClose()
      }, 1000)

    } catch (err: any) {
      console.error('Upload error:', err)
      setError(err.message || 'Failed to upload file')
    } finally {
      setIsUploading(false)
    }
  }

  const getFileIcon = () => {
    if (!file) return <File className="h-12 w-12 text-gray-400" />

    if (file.type.startsWith('image/')) {
      return <ImageIcon className="h-12 w-12 text-blue-500" />
    } else if (file.type.startsWith('video/')) {
      return <Video className="h-12 w-12 text-purple-500" />
    } else if (file.type.includes('pdf')) {
      return <FileText className="h-12 w-12 text-red-500" />
    } else {
      return <File className="h-12 w-12 text-gray-500" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="rounded-lg bg-white p-6 shadow-lg">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Upload File</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {!file ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            'cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-colors',
            isDragging
              ? 'border-[#007a5a] bg-green-50'
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          )}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-sm font-medium text-gray-900">
            Drop a file here, or click to browse
          </p>
          <p className="mt-1 text-xs text-gray-500">
            Maximum file size: 100 MB
          </p>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleInputChange}
            className="hidden"
          />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-start space-x-4 rounded-lg border border-gray-200 p-4">
            {getFileIcon()}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">{file.name}</p>
              <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
              {isUploading && (
                <div className="mt-2">
                  <div className="h-2 w-full rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-[#007a5a] transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              )}
            </div>
            {!isUploading && (
              <button
                onClick={() => setFile(null)}
                className="rounded p-1 hover:bg-gray-100"
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            )}
          </div>

          {error && (
            <div className="rounded bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button
              variant="secondary"
              onClick={() => setFile(null)}
              disabled={isUploading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
