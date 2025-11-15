'use client'

import { useEffect, useRef, useState } from 'react'
import { Hash, Lock, Users, Pin, Search, Phone, Video, Info } from 'lucide-react'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useChatStore } from '@/stores/chat-store'
import { useAuthStore } from '@/stores/auth-store'
import { apiClient } from '@/lib/api-client'
import { wsClient } from '@/lib/websocket-client'
import { MessageItem } from '@/components/chat/message-item'
import { MessageInput } from '@/components/chat/message-input'
import { cn } from '@/lib/utils'

export default function WorkspacePage() {
  const user = useAuthStore((state) => state.user)
  const { activeChannelId, channels } = useWorkspaceStore()
  const { messages, setMessages, addMessage, updateMessage, deleteMessage } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(false)

  const activeChannel = channels.find((ch) => ch.channel_id === activeChannelId)
  const channelMessages = activeChannelId ? messages[activeChannelId] || [] : []

  useEffect(() => {
    if (activeChannelId) {
      loadMessages()
      setupWebSocket()
    }

    return () => {
      if (activeChannelId) {
        wsClient.leaveChannel(activeChannelId)
      }
    }
  }, [activeChannelId])

  useEffect(() => {
    scrollToBottom()
  }, [channelMessages])

  const loadMessages = async () => {
    if (!activeChannelId) return

    setIsLoading(true)
    try {
      const data = await apiClient.getMessages(activeChannelId, 100, 0)
      setMessages(activeChannelId, data)
    } catch (error) {
      console.error('Failed to load messages:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const setupWebSocket = () => {
    if (!activeChannelId) return

    // Join channel for real-time updates
    wsClient.joinChannel(activeChannelId)

    // Listen for new messages
    wsClient.onMessage((message) => {
      if (message.channel_id === activeChannelId) {
        addMessage(activeChannelId, message)
      }
    })

    // Listen for message updates
    wsClient.onMessageUpdated((message) => {
      if (message.channel_id === activeChannelId) {
        updateMessage(activeChannelId, message.message_id, message)
      }
    })

    // Listen for message deletions
    wsClient.onMessageDeleted((data) => {
      if (data.channel_id === activeChannelId) {
        deleteMessage(activeChannelId, data.message_id)
      }
    })
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async (content: string) => {
    if (!activeChannelId) return

    try {
      const newMessage = await apiClient.sendMessage(activeChannelId, content)
      // Message will be added via WebSocket event
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const handleReaction = async (messageId: string, emoji: string) => {
    try {
      await apiClient.addReaction(messageId, emoji)
    } catch (error) {
      console.error('Failed to add reaction:', error)
    }
  }

  const handleStartTyping = () => {
    if (activeChannelId) {
      apiClient.startTyping(activeChannelId)
    }
  }

  const handleStopTyping = () => {
    if (activeChannelId) {
      apiClient.stopTyping(activeChannelId)
    }
  }

  if (!activeChannel) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-50">
        <div className="text-center">
          <Hash className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No channel selected</h3>
          <p className="mt-2 text-sm text-gray-500">
            Select a channel from the sidebar to start messaging
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Channel Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {activeChannel.is_private ? (
              <Lock className="h-5 w-5 text-gray-600" />
            ) : (
              <Hash className="h-5 w-5 text-gray-600" />
            )}
            <h2 className="text-lg font-bold text-gray-900">{activeChannel.name}</h2>
          </div>
          {activeChannel.topic && (
            <span className="text-sm text-gray-600">| {activeChannel.topic}</span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button className="rounded p-2 hover:bg-gray-100" title="Search in channel">
            <Search className="h-5 w-5 text-gray-600" />
          </button>
          <button className="rounded p-2 hover:bg-gray-100" title="Start a call">
            <Phone className="h-5 w-5 text-gray-600" />
          </button>
          <button className="rounded p-2 hover:bg-gray-100" title="Start a video call">
            <Video className="h-5 w-5 text-gray-600" />
          </button>
          <button className="rounded p-2 hover:bg-gray-100" title="View members">
            <Users className="h-5 w-5 text-gray-600" />
          </button>
          <button className="rounded p-2 hover:bg-gray-100" title="Channel details">
            <Info className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-[#007a5a]" />
          </div>
        ) : channelMessages.length === 0 ? (
          <div className="flex h-full items-center justify-center px-5">
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
                {activeChannel.is_private ? (
                  <Lock className="h-8 w-8 text-gray-400" />
                ) : (
                  <Hash className="h-8 w-8 text-gray-400" />
                )}
              </div>
              <h3 className="mt-4 text-xl font-bold text-gray-900">
                This is the beginning of #{activeChannel.name}
              </h3>
              {activeChannel.description && (
                <p className="mt-2 text-gray-600">{activeChannel.description}</p>
              )}
            </div>
          </div>
        ) : (
          <div className="py-4">
            {channelMessages.map((message) => (
              <MessageItem
                key={message.message_id}
                message={message}
                onReact={(emoji) => handleReaction(message.message_id, emoji)}
                onReply={() => {}}
                onEdit={() => {}}
                onDelete={() => {}}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Input */}
      <MessageInput
        channelName={`#${activeChannel.name}`}
        onSendMessage={handleSendMessage}
        onTyping={handleStartTyping}
        onStopTyping={handleStopTyping}
      />
    </div>
  )
}
