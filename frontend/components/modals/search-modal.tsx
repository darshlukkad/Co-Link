'use client'

import { useState, useEffect } from 'react'
import { Search, X, Hash, File, User } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Message, FileAttachment } from '@/types'
import { formatMessageTime } from '@/lib/utils'
import { Avatar } from '@/components/ui/avatar'

interface SearchModalProps {
  isOpen: boolean
  onClose: () => void
  workspaceId: string
  onSelectMessage?: (message: Message) => void
  onSelectFile?: (file: FileAttachment) => void
}

export function SearchModal({
  isOpen,
  onClose,
  workspaceId,
  onSelectMessage,
  onSelectFile,
}: SearchModalProps) {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [files, setFiles] = useState<FileAttachment[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'all' | 'messages' | 'files'>('all')

  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setMessages([])
      setFiles([])
    }
  }, [isOpen])

  useEffect(() => {
    if (query.trim().length < 2) {
      setMessages([])
      setFiles([])
      return
    }

    const delaySearch = setTimeout(() => {
      performSearch()
    }, 300) // Debounce

    return () => clearTimeout(delaySearch)
  }, [query, workspaceId])

  const performSearch = async () => {
    setIsLoading(true)
    try {
      const results = await apiClient.unifiedSearch(query, workspaceId)
      setMessages(results.messages || [])
      setFiles(results.files || [])
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMessageClick = (message: Message) => {
    if (onSelectMessage) {
      onSelectMessage(message)
    }
    onClose()
  }

  const handleFileClick = (file: FileAttachment) => {
    if (onSelectFile) {
      onSelectFile(file)
    }
    onClose()
  }

  if (!isOpen) return null

  const showMessages = activeTab === 'all' || activeTab === 'messages'
  const showFiles = activeTab === 'all' || activeTab === 'files'

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl rounded-lg bg-white shadow-2xl">
        {/* Search Input */}
        <div className="border-b border-gray-200 p-4">
          <div className="flex items-center space-x-3">
            <Search className="h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search messages, files, and people..."
              className="flex-1 bg-transparent text-lg outline-none placeholder-gray-400"
              autoFocus
            />
            <button
              onClick={onClose}
              className="rounded p-1 hover:bg-gray-100"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* Tabs */}
          <div className="mt-4 flex space-x-2">
            <button
              onClick={() => setActiveTab('all')}
              className={`rounded px-3 py-1 text-sm font-medium ${
                activeTab === 'all'
                  ? 'bg-[#007a5a] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All Results
            </button>
            <button
              onClick={() => setActiveTab('messages')}
              className={`rounded px-3 py-1 text-sm font-medium ${
                activeTab === 'messages'
                  ? 'bg-[#007a5a] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Messages ({messages.length})
            </button>
            <button
              onClick={() => setActiveTab('files')}
              className={`rounded px-3 py-1 text-sm font-medium ${
                activeTab === 'files'
                  ? 'bg-[#007a5a] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Files ({files.length})
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-[#007a5a]" />
            </div>
          ) : query.trim().length < 2 ? (
            <div className="py-12 text-center">
              <Search className="mx-auto h-12 w-12 text-gray-300" />
              <p className="mt-4 text-sm text-gray-500">
                Start typing to search...
              </p>
            </div>
          ) : messages.length === 0 && files.length === 0 ? (
            <div className="py-12 text-center">
              <Search className="mx-auto h-12 w-12 text-gray-300" />
              <p className="mt-4 text-sm text-gray-500">
                No results found for "{query}"
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {/* Messages */}
              {showMessages && messages.length > 0 && (
                <div>
                  <div className="bg-gray-50 px-4 py-2">
                    <h3 className="text-xs font-semibold uppercase text-gray-500">
                      Messages
                    </h3>
                  </div>
                  {messages.map((message) => (
                    <button
                      key={message.message_id}
                      onClick={() => handleMessageClick(message)}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50"
                    >
                      <div className="flex items-start space-x-3">
                        <Avatar
                          src={message.user?.avatar_url}
                          name={message.user?.display_name || 'Unknown'}
                          userId={message.user_id}
                          size="sm"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-baseline space-x-2">
                            <span className="font-semibold text-sm">
                              {message.user?.display_name || 'Unknown'}
                            </span>
                            <span className="text-xs text-gray-500">
                              {formatMessageTime(message.created_at)}
                            </span>
                          </div>
                          <p className="mt-0.5 text-sm text-gray-600 truncate">
                            {message.content}
                          </p>
                        </div>
                        <Hash className="h-4 w-4 text-gray-400" />
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Files */}
              {showFiles && files.length > 0 && (
                <div>
                  <div className="bg-gray-50 px-4 py-2">
                    <h3 className="text-xs font-semibold uppercase text-gray-500">
                      Files
                    </h3>
                  </div>
                  {files.map((file) => (
                    <button
                      key={file.file_id}
                      onClick={() => handleFileClick(file)}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-3">
                        <File className="h-8 w-8 flex-shrink-0 text-gray-400" />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">
                            {file.filename}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(file.size_bytes / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-4 py-3">
          <p className="text-xs text-gray-500">
            Press <kbd className="rounded bg-gray-100 px-1.5 py-0.5 font-mono">Esc</kbd> to close
          </p>
        </div>
      </div>
    </div>
  )
}
