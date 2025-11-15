'use client'

import { useEffect, useState } from 'react'
import { Hash, Lock, Plus, ChevronDown, MessageSquare, LogOut } from 'lucide-react'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useAuthStore } from '@/stores/auth-store'
import { apiClient } from '@/lib/api-client'
import { Avatar } from '@/components/ui/avatar'
import { CreateChannelModal } from '@/components/modals/create-channel-modal'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'

export default function Sidebar() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const {
    channels,
    directMessages,
    activeChannelId,
    activeDMId,
    setChannels,
    setDirectMessages,
    setActiveChannel,
    setActiveDM,
    addChannel,
  } = useWorkspaceStore()

  const [isChannelsOpen, setIsChannelsOpen] = useState(true)
  const [isDMsOpen, setIsDMsOpen] = useState(true)
  const [isCreateChannelOpen, setIsCreateChannelOpen] = useState(false)
  const WORKSPACE_ID = '550e8400-e29b-41d4-a716-446655440000' // Default workspace

  useEffect(() => {
    loadChannelsAndDMs()
  }, [])

  const loadChannelsAndDMs = async () => {
    try {
      const [channelsData, dmsData] = await Promise.all([
        apiClient.getChannels(WORKSPACE_ID),
        apiClient.getDMs(WORKSPACE_ID),
      ])
      setChannels(channelsData)
      setDirectMessages(dmsData)

      // Auto-select first channel if none selected
      if (!activeChannelId && !activeDMId && channelsData.length > 0) {
        setActiveChannel(channelsData[0].channel_id)
      }
    } catch (error) {
      console.error('Failed to load channels/DMs:', error)
    }
  }

  const handleLogout = async () => {
    await apiClient.logout()
    logout()
    router.push('/login')
  }

  const handleChannelCreated = (channel: any) => {
    addChannel(channel)
    setActiveChannel(channel.channel_id)
  }

  if (!user) return null

  return (
    <>
      <div className="flex h-full w-64 flex-col bg-[#3f0e40] text-white">
        {/* Workspace Header */}
        <button className="flex items-center justify-between border-b border-[#522653] px-4 py-3 text-left hover:bg-[#350d36]">
          <div className="flex items-center space-x-2">
            <div className="flex h-9 w-9 items-center justify-center rounded bg-white text-[#3f0e40] font-bold text-lg">
              C
            </div>
            <div>
              <h2 className="font-bold">CoLink Workspace</h2>
            </div>
          </div>
          <ChevronDown className="h-4 w-4" />
        </button>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Threads, DMs, etc. */}
          <div className="border-b border-[#522653] px-3 py-2">
            <SidebarItem icon={MessageSquare} label="Threads" active={false} onClick={() => {}} />
            <SidebarItem icon={MessageSquare} label="All DMs" active={false} onClick={() => {}} />
          </div>

          {/* Channels */}
          <div className="px-3 py-2">
            <button
              onClick={() => setIsChannelsOpen(!isChannelsOpen)}
              className="mb-1 flex w-full items-center justify-between rounded px-2 py-1 text-sm hover:bg-[#350d36]"
            >
              <span className="font-semibold">Channels</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setIsCreateChannelOpen(true)
                }}
                className="rounded p-0.5 hover:bg-[#1a1d20]"
                title="Create channel"
              >
                <Plus className="h-4 w-4" />
              </button>
            </button>
            {isChannelsOpen && (
              <div className="space-y-0.5">
                {channels.map((channel) => (
                  <button
                    key={channel.channel_id}
                    onClick={() => setActiveChannel(channel.channel_id)}
                    className={cn(
                      'flex w-full items-center space-x-2 rounded px-2 py-1 text-sm hover:bg-[#350d36]',
                      activeChannelId === channel.channel_id && 'bg-[#1164a3] text-white'
                    )}
                  >
                    {channel.is_private ? (
                      <Lock className="h-4 w-4 flex-shrink-0" />
                    ) : (
                      <Hash className="h-4 w-4 flex-shrink-0" />
                    )}
                    <span className="truncate">{channel.name}</span>
                    {channel.unread_count && channel.unread_count > 0 && (
                      <span className="ml-auto rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold">
                        {channel.unread_count}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Direct Messages */}
          <div className="px-3 py-2">
            <button
              onClick={() => setIsDMsOpen(!isDMsOpen)}
              className="mb-1 flex w-full items-center justify-between rounded px-2 py-1 text-sm hover:bg-[#350d36]"
            >
              <span className="font-semibold">Direct messages</span>
              <Plus className="h-4 w-4" />
            </button>
            {isDMsOpen && (
              <div className="space-y-0.5">
                {directMessages.map((dm) => {
                  const otherUser = dm.participants?.find((p) => p.user_id !== user.user_id)
                  if (!otherUser) return null

                  return (
                    <button
                      key={dm.dm_id}
                      onClick={() => setActiveDM(dm.dm_id)}
                      className={cn(
                        'flex w-full items-center space-x-2 rounded px-2 py-1 text-sm hover:bg-[#350d36]',
                        activeDMId === dm.dm_id && 'bg-[#1164a3] text-white'
                      )}
                    >
                      <Avatar
                        src={otherUser.avatar_url}
                        name={otherUser.display_name}
                        userId={otherUser.user_id}
                        size="sm"
                        status="online"
                      />
                      <span className="truncate">{otherUser.display_name}</span>
                      {dm.unread_count && dm.unread_count > 0 && (
                        <span className="ml-auto rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold">
                          {dm.unread_count}
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* User Profile */}
        <div className="border-t border-[#522653] p-2">
          <div className="group relative">
            <button className="flex w-full items-center space-x-2 rounded px-2 py-2 hover:bg-[#350d36]">
              <Avatar
                src={user.avatar_url}
                name={user.display_name}
                userId={user.user_id}
                size="md"
                status="online"
              />
              <div className="flex-1 text-left">
                <p className="text-sm font-semibold truncate">{user.display_name}</p>
                <p className="text-xs text-gray-300 truncate">Active</p>
              </div>
            </button>

            {/* Logout button on hover */}
            <button
              onClick={handleLogout}
              className="absolute right-2 top-2 hidden rounded bg-red-600 p-1.5 text-white hover:bg-red-700 group-hover:block"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Create Channel Modal */}
      <CreateChannelModal
        isOpen={isCreateChannelOpen}
        onClose={() => setIsCreateChannelOpen(false)}
        workspaceId={WORKSPACE_ID}
        onChannelCreated={handleChannelCreated}
      />
    </>
  )
}

interface SidebarItemProps {
  icon: any
  label: string
  active: boolean
  onClick: () => void
}

function SidebarItem({ icon: Icon, label, active, onClick }: SidebarItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex w-full items-center space-x-2 rounded px-2 py-1 text-sm hover:bg-[#350d36]',
        active && 'bg-[#1164a3] text-white'
      )}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </button>
  )
}
