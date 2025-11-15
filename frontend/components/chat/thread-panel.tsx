'use client'

import { useEffect, useState } from 'react'
import { X, ArrowLeft } from 'lucide-react'
import { Message } from '@/types'
import { apiClient } from '@/lib/api-client'
import { useChatStore } from '@/stores/chat-store'
import { MessageItem } from './message-item'
import { MessageInput } from './message-input'
import { Avatar } from '@/components/ui/avatar'
import { formatMessageTime } from '@/lib/utils'

interface ThreadPanelProps {
  messageId: string
  onClose: () => void
}

export function ThreadPanel({ messageId, onClose }: ThreadPanelProps) {
  const [parentMessage, setParentMessage] = useState<Message | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { threadMessages, setThreadMessages, addThreadMessage } = useChatStore()

  useEffect(() => {
    loadThread()
  }, [messageId])

  const loadThread = async () => {
    setIsLoading(true)
    try {
      // Load parent message (would need API endpoint)
      // For now, we'll load thread replies
      const replies = await apiClient.getThreadReplies(messageId)
      setThreadMessages(replies)
    } catch (error) {
      console.error('Failed to load thread:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendReply = async (content: string) => {
    try {
      const reply = await apiClient.sendThreadReply(messageId, content)
      addThreadMessage(reply)
    } catch (error) {
      console.error('Failed to send reply:', error)
    }
  }

  return (
    <div className="flex h-full w-96 flex-col border-l border-gray-200 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div className="flex items-center space-x-2">
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-gray-100 md:hidden"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h2 className="font-bold text-gray-900">Thread</h2>
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 hover:bg-gray-100"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Thread Content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-[#007a5a]" />
          </div>
        ) : (
          <div className="space-y-4 p-4">
            {/* Parent Message */}
            {parentMessage && (
              <div className="rounded-lg bg-gray-50 p-4">
                <div className="flex items-start space-x-3">
                  <Avatar
                    src={parentMessage.user?.avatar_url}
                    name={parentMessage.user?.display_name || 'Unknown'}
                    userId={parentMessage.user_id}
                    size="md"
                  />
                  <div className="flex-1">
                    <div className="flex items-baseline space-x-2">
                      <span className="font-semibold text-sm">
                        {parentMessage.user?.display_name || 'Unknown'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatMessageTime(parentMessage.created_at)}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                      {parentMessage.content}
                    </p>
                  </div>
                </div>
                <div className="mt-3 border-t border-gray-200 pt-3">
                  <p className="text-sm font-medium text-gray-700">
                    {threadMessages.length}{' '}
                    {threadMessages.length === 1 ? 'reply' : 'replies'}
                  </p>
                </div>
              </div>
            )}

            {/* Thread Replies */}
            <div className="space-y-2">
              {threadMessages.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-sm text-gray-500">
                    No replies yet. Start the conversation!
                  </p>
                </div>
              ) : (
                threadMessages.map((message) => (
                  <MessageItem
                    key={message.message_id}
                    message={message}
                    onReact={(emoji) => {}}
                    onReply={() => {}}
                    onEdit={() => {}}
                    onDelete={() => {}}
                  />
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Reply Input */}
      <div className="border-t border-gray-200">
        <MessageInput
          placeholder="Reply to thread..."
          onSendMessage={handleSendReply}
        />
      </div>
    </div>
  )
}
