'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, AtSign, Bold, Italic, Strikethrough, Code } from 'lucide-react'
import { cn } from '@/lib/utils'
import { EmojiPicker } from '@/components/ui/emoji-picker'

interface MessageInputProps {
  channelName?: string
  onSendMessage: (content: string) => void
  onTyping?: () => void
  onStopTyping?: () => void
  placeholder?: string
}

export function MessageInput({
  channelName,
  onSendMessage,
  onTyping,
  onStopTyping,
  placeholder,
}: MessageInputProps) {
  const [message, setMessage] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }

    // Typing indicator
    if (onTyping) {
      onTyping()

      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }

      typingTimeoutRef.current = setTimeout(() => {
        if (onStopTyping) {
          onStopTyping()
        }
      }, 3000)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      onSendMessage(message.trim())
      setMessage('')

      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }

      if (onStopTyping) {
        onStopTyping()
      }

      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleEmojiSelect = (emoji: string) => {
    const textarea = textareaRef.current
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const newMessage = message.slice(0, start) + emoji + message.slice(end)

    setMessage(newMessage)

    // Set cursor position after emoji
    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + emoji.length
      textarea.focus()
    }, 0)
  }

  return (
    <div className="border-t border-gray-200 px-5 py-4">
      <form onSubmit={handleSubmit}>
        <div
          className={cn(
            'rounded-lg border border-gray-300 bg-white transition-all',
            isFocused && 'border-[#007a5a] ring-1 ring-[#007a5a]'
          )}
        >
          {/* Formatting Toolbar */}
          <div className="flex items-center space-x-1 border-b border-gray-200 px-3 py-2">
            <button
              type="button"
              className="rounded p-1 hover:bg-gray-100"
              title="Bold"
            >
              <Bold className="h-4 w-4 text-gray-600" />
            </button>
            <button
              type="button"
              className="rounded p-1 hover:bg-gray-100"
              title="Italic"
            >
              <Italic className="h-4 w-4 text-gray-600" />
            </button>
            <button
              type="button"
              className="rounded p-1 hover:bg-gray-100"
              title="Strikethrough"
            >
              <Strikethrough className="h-4 w-4 text-gray-600" />
            </button>
            <button
              type="button"
              className="rounded p-1 hover:bg-gray-100"
              title="Code"
            >
              <Code className="h-4 w-4 text-gray-600" />
            </button>
            <div className="h-4 w-px bg-gray-300 mx-1" />
            <button
              type="button"
              className="rounded p-1 hover:bg-gray-100"
              title="Attach file"
            >
              <Paperclip className="h-4 w-4 text-gray-600" />
            </button>
            <EmojiPicker onEmojiSelect={handleEmojiSelect} />
            <button
              type="button"
              className="rounded p-1 hover:bg-gray-100"
              title="Mention"
            >
              <AtSign className="h-4 w-4 text-gray-600" />
            </button>
          </div>

          {/* Message Input */}
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholder || `Message ${channelName || ''}`}
              className="w-full resize-none border-0 px-3 py-3 text-sm placeholder-gray-400 focus:outline-none"
              rows={1}
              style={{ maxHeight: '200px' }}
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-3 py-2">
            <div className="text-xs text-gray-500">
              <span className="font-medium">Enter</span> to send, <span className="font-medium">Shift + Enter</span> for new line
            </div>
            <button
              type="submit"
              disabled={!message.trim()}
              className={cn(
                'flex items-center space-x-1.5 rounded px-3 py-1.5 text-sm font-medium transition-colors',
                message.trim()
                  ? 'bg-[#007a5a] text-white hover:bg-[#006644]'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              )}
            >
              <Send className="h-4 w-4" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
