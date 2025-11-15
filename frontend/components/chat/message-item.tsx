'use client'

import { useState } from 'react'
import { MoreHorizontal, Smile, MessageSquare, Pencil, Trash2 } from 'lucide-react'
import { Message } from '@/types'
import { Avatar } from '@/components/ui/avatar'
import { formatMessageTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface MessageItemProps {
  message: Message
  onReact: (emoji: string) => void
  onReply: () => void
  onEdit: () => void
  onDelete: () => void
}

export function MessageItem({ message, onReact, onReply, onEdit, onDelete }: MessageItemProps) {
  const [showActions, setShowActions] = useState(false)
  const [showReactions, setShowReactions] = useState(false)

  if (message.is_deleted) {
    return (
      <div className="group px-5 py-2 hover:bg-gray-50">
        <div className="flex space-x-3">
          <div className="flex-shrink-0">
            <Avatar
              src={message.user?.avatar_url}
              name={message.user?.display_name || 'Deleted User'}
              userId={message.user_id}
              size="md"
            />
          </div>
          <div className="flex-1">
            <div className="text-sm text-gray-500 italic">
              This message was deleted
            </div>
          </div>
        </div>
      </div>
    )
  }

  const quickEmojis = ['👍', '😄', '🎉', '❤️', '🚀', '👀']

  return (
    <div
      className="group relative px-3 py-2 md:px-5 hover:bg-gray-50 transition-colors animate-fadeIn"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false)
        setShowReactions(false)
      }}
    >
      <div className="flex space-x-3">
        <div className="flex-shrink-0">
          <Avatar
            src={message.user?.avatar_url}
            name={message.user?.display_name || 'Unknown'}
            userId={message.user_id}
            size="md"
            status="online"
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline space-x-2">
            <span className="font-semibold text-sm text-gray-900">
              {message.user?.display_name || 'Unknown User'}
            </span>
            <span className="text-xs text-gray-500">
              {formatMessageTime(message.created_at)}
            </span>
            {message.is_edited && (
              <span className="text-xs text-gray-400">(edited)</span>
            )}
          </div>
          <div className="mt-0.5 text-sm text-gray-900 whitespace-pre-wrap break-words">
            {message.content}
          </div>

          {/* Reactions */}
          {message.reactions && message.reactions.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {Object.entries(
                message.reactions.reduce((acc, reaction) => {
                  acc[reaction.emoji] = (acc[reaction.emoji] || 0) + 1
                  return acc
                }, {} as Record<string, number>)
              ).map(([emoji, count]) => (
                <button
                  key={emoji}
                  onClick={() => onReact(emoji)}
                  className="inline-flex items-center space-x-1 rounded-full border border-slack-green bg-blue-50 px-2 py-0.5 text-sm hover:bg-blue-100 transition-colors"
                >
                  <span>{emoji}</span>
                  <span className="text-xs font-medium text-slack-green">{count}</span>
                </button>
              ))}
            </div>
          )}

          {/* Thread replies count */}
          {message.thread_reply_count && message.thread_reply_count > 0 && (
            <button
              onClick={onReply}
              className="mt-1 inline-flex items-center space-x-1 text-sm text-slack-green hover:underline"
            >
              <MessageSquare className="h-4 w-4" />
              <span>{message.thread_reply_count} {message.thread_reply_count === 1 ? 'reply' : 'replies'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Message Actions */}
      {showActions && (
        <div className="absolute right-3 md:right-4 top-2 flex items-center space-x-0.5 rounded-lg border border-gray-200 bg-white shadow-md animate-scale-in">
          <button
            onClick={() => setShowReactions(!showReactions)}
            className="rounded p-1.5 hover:bg-gray-100 transition-colors"
            title="Add reaction"
          >
            <Smile className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={onReply}
            className="rounded p-1.5 hover:bg-gray-100 transition-colors"
            title="Reply in thread"
          >
            <MessageSquare className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={onEdit}
            className="hidden sm:block rounded p-1.5 hover:bg-gray-100 transition-colors"
            title="Edit message"
          >
            <Pencil className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={onDelete}
            className="hidden sm:block rounded p-1.5 hover:bg-gray-100 transition-colors"
            title="Delete message"
          >
            <Trash2 className="h-4 w-4 text-gray-600" />
          </button>
          <button className="rounded p-1.5 hover:bg-gray-100 transition-colors" title="More actions">
            <MoreHorizontal className="h-4 w-4 text-gray-600" />
          </button>
        </div>
      )}

      {/* Quick Reactions Picker */}
      {showReactions && (
        <div className="absolute right-3 md:right-4 top-12 z-10 flex items-center space-x-1 rounded-lg border border-gray-200 bg-white p-2 shadow-lg animate-scale-in">
          {quickEmojis.map((emoji) => (
            <button
              key={emoji}
              onClick={() => {
                onReact(emoji)
                setShowReactions(false)
              }}
              className="rounded p-1 text-xl hover:bg-gray-100 transition-colors"
            >
              {emoji}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
