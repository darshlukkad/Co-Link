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
  isGrouped?: boolean // Whether this message is grouped with the previous one
  showDateDivider?: boolean // Whether to show a date divider above
  dateDividerText?: string // Text for the date divider
}

export function MessageItem({
  message,
  onReact,
  onReply,
  onEdit,
  onDelete,
  isGrouped = false,
  showDateDivider = false,
  dateDividerText
}: MessageItemProps) {
  const [showActions, setShowActions] = useState(false)
  const [showReactions, setShowReactions] = useState(false)

  if (message.is_deleted) {
    return (
      <>
        {showDateDivider && dateDividerText && (
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-xs font-semibold text-gray-700">
                {dateDividerText}
              </span>
            </div>
          </div>
        )}
        <div className="group px-5 py-2 hover:bg-gray-50">
          <div className="flex space-x-3">
            <div className="flex-shrink-0 w-9">
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
      </>
    )
  }

  const quickEmojis = ['👍', '😄', '🎉', '❤️', '🚀', '👀']

  return (
    <>
      {showDateDivider && dateDividerText && (
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-white px-3 text-xs font-semibold text-gray-700">
              {dateDividerText}
            </span>
          </div>
        </div>
      )}
      <div
        className={cn(
          "group relative px-3 py-1 md:px-5 hover:bg-gray-50 transition-colors",
          !isGrouped && "mt-2 pt-2",
          isGrouped && "py-0.5"
        )}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => {
          setShowActions(false)
          setShowReactions(false)
        }}
      >
        <div className="flex space-x-3">
          {/* Avatar column - always same width */}
          <div className="flex-shrink-0 w-9">
            {!isGrouped && (
              <Avatar
                src={message.user?.avatar_url}
                name={message.user?.display_name || 'Unknown'}
                userId={message.user_id}
                size="md"
                status="online"
              />
            )}
            {isGrouped && (
              <time className="text-[11px] text-transparent group-hover:text-gray-500 transition-colors text-right block leading-[22px]">
                {new Date(message.created_at).toLocaleTimeString('en-US', {
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: true
                })}
              </time>
            )}
          </div>

          <div className="flex-1 min-w-0">
            {!isGrouped && (
              <div className="flex items-baseline space-x-2 mb-0.5">
                <span className="font-bold text-[15px] text-gray-900 hover:underline cursor-pointer">
                  {message.user?.display_name || 'Unknown User'}
                </span>
                <span className="text-xs text-gray-500 font-normal">
                  {formatMessageTime(message.created_at)}
                </span>
                {message.is_edited && (
                  <span className="text-xs text-gray-400">(edited)</span>
                )}
              </div>
            )}
            <div className={cn(
              "text-[15px] text-gray-900 whitespace-pre-wrap break-words leading-[22px]",
              isGrouped && "py-0"
            )}>
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
    </>
  )
}
