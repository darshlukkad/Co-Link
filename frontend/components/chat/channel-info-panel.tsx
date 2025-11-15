'use client'

import { X, Hash, Lock, Bell, Pin, Users, Settings, Archive } from 'lucide-react'
import { Channel } from '@/types'
import { Avatar } from '@/components/ui/avatar'

interface ChannelInfoPanelProps {
  channel: Channel
  onClose: () => void
  memberCount?: number
  pinnedMessages?: number
}

export function ChannelInfoPanel({
  channel,
  onClose,
  memberCount = 0,
  pinnedMessages = 0
}: ChannelInfoPanelProps) {
  return (
    <div className="w-full md:w-96 bg-white border-l border-gray-200 flex flex-col h-full animate-slide-in-right">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 p-4">
        <h2 className="text-lg font-bold text-gray-900">Details</h2>
        <button
          onClick={onClose}
          className="rounded p-1 hover:bg-gray-100 transition-colors"
          aria-label="Close"
        >
          <X className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Channel Name */}
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-3">
            {channel.is_private ? (
              <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-gray-100">
                <Lock className="h-7 w-7 text-gray-600" />
              </div>
            ) : (
              <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-gray-100">
                <Hash className="h-7 w-7 text-gray-600" />
              </div>
            )}
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900">
                {channel.is_private ? '' : '#'}{channel.name}
              </h3>
              {channel.is_private && (
                <p className="text-sm text-gray-600">Private channel</p>
              )}
            </div>
          </div>

          {/* Topic */}
          {channel.topic && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-1">Topic</h4>
              <p className="text-sm text-gray-900">{channel.topic}</p>
            </div>
          )}

          {/* Description */}
          {channel.description && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-1">Description</h4>
              <p className="text-sm text-gray-900">{channel.description}</p>
            </div>
          )}

          {/* Created */}
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-1">Created</h4>
            <p className="text-sm text-gray-600">
              {new Date(channel.created_at).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric'
              })}
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="border-b border-gray-200 py-2">
          <button className="flex w-full items-center space-x-3 px-6 py-3 hover:bg-gray-50 transition-colors">
            <Bell className="h-5 w-5 text-gray-600" />
            <div className="flex-1 text-left">
              <div className="text-sm font-medium text-gray-900">Notifications</div>
              <div className="text-xs text-gray-500">Get notified for all messages</div>
            </div>
          </button>

          <button className="flex w-full items-center space-x-3 px-6 py-3 hover:bg-gray-50 transition-colors">
            <Pin className="h-5 w-5 text-gray-600" />
            <div className="flex-1 text-left">
              <div className="text-sm font-medium text-gray-900">Pinned messages</div>
              <div className="text-xs text-gray-500">
                {pinnedMessages > 0 ? `${pinnedMessages} pinned` : 'No pinned messages'}
              </div>
            </div>
          </button>

          <button className="flex w-full items-center space-x-3 px-6 py-3 hover:bg-gray-50 transition-colors">
            <Users className="h-5 w-5 text-gray-600" />
            <div className="flex-1 text-left">
              <div className="text-sm font-medium text-gray-900">Members</div>
              <div className="text-xs text-gray-500">
                {memberCount > 0 ? `${memberCount} members` : 'View members'}
              </div>
            </div>
          </button>
        </div>

        {/* Settings */}
        <div className="border-b border-gray-200 py-2">
          <button className="flex w-full items-center space-x-3 px-6 py-3 hover:bg-gray-50 transition-colors">
            <Settings className="h-5 w-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-900">Channel settings</span>
          </button>
        </div>

        {/* Leave Channel */}
        <div className="py-2">
          <button className="flex w-full items-center space-x-3 px-6 py-3 hover:bg-red-50 text-red-600 transition-colors">
            <Archive className="h-5 w-5" />
            <span className="text-sm font-medium">Leave channel</span>
          </button>
        </div>
      </div>
    </div>
  )
}
