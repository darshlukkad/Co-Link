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

interface SidebarProps {
  onNavigate?: () => void
}

export default function Sidebar({ onNavigate }: SidebarProps = {}) {
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

  const handleNavigation = (action: () => void) => {
    action()
    onNavigate?.()
  }

  return (
    <>
      <div className="flex h-full w-64 flex-col bg-slack-purple text-white">
        {/* Workspace Header */}
        <button className="flex items-center justify-between border-b border-slack-purple-border px-4 py-3.5 text-left hover:bg-slack-purple-hover transition-all duration-100">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded bg-white text-slack-purple font-black text-lg">
              C
            </div>
            <div>
              <h2 className="font-black text-[15px] leading-tight">CoLink Workspace</h2>
            </div>
          </div>
          <ChevronDown className="h-4 w-4 opacity-70" />
        </button>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Threads, DMs, etc. */}
          <div className="border-b border-slack-purple-border px-3 py-3">
            <SidebarItem icon={MessageSquare} label="Threads" active={false} onClick={() => {}} />
            <SidebarItem icon={MessageSquare} label="All DMs" active={false} onClick={() => {}} />
          </div>

          {/* Channels */}
          <div className="px-3 py-3">
            <button
              onClick={() => setIsChannelsOpen(!isChannelsOpen)}
              className="mb-1 flex w-full items-center justify-between rounded px-3 py-0.5 text-[15px] hover:bg-slack-purple-hover transition-all duration-75"
            >
              <span className="font-bold text-white/70">Channels</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setIsCreateChannelOpen(true)
                }}
                className="rounded p-1 hover:bg-slack-purple-darker transition-all duration-75"
                title="Create channel"
              >
                <Plus className="h-[18px] w-[18px]" />
              </button>
            </button>
            {isChannelsOpen && (
              <div className="space-y-0">
                {channels.map((channel) => (
                  <button
                    key={channel.channel_id}
                    onClick={() => handleNavigation(() => setActiveChannel(channel.channel_id))}
                    className={cn(
                      'flex w-full items-center gap-1.5 rounded px-3 py-1 text-[15px] hover:bg-slack-purple-hover transition-all duration-75',
                      activeChannelId === channel.channel_id && 'bg-slack-purple-active text-white font-bold'
                    )}
                  >
                    {channel.is_private ? (
                      <Lock className="h-[18px] w-[18px] flex-shrink-0" />
                    ) : (
                      <Hash className="h-[18px] w-[18px] flex-shrink-0" />
                    )}
                    <span className="truncate">{channel.name}</span>
                    {channel.unread_count && channel.unread_count > 0 && (
                      <span className="ml-auto rounded-full bg-slack-red px-1.5 py-0.5 text-xs font-bold">
                        {channel.unread_count}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Direct Messages */}
          <div className="px-3 py-3">
            <button
              onClick={() => setIsDMsOpen(!isDMsOpen)}
              className="mb-1 flex w-full items-center justify-between rounded px-3 py-0.5 text-[15px] hover:bg-slack-purple-hover transition-all duration-75"
            >
              <span className="font-bold text-white/70">Direct messages</span>
              <Plus className="h-[18px] w-[18px]" />
            </button>
            {isDMsOpen && (
              <div className="space-y-0">
                {directMessages.map((dm) => {
                  const otherUser = dm.participants?.find((p) => p.user_id !== user.user_id)
                  if (!otherUser) return null

                  return (
                    <button
                      key={dm.dm_id}
                      onClick={() => handleNavigation(() => setActiveDM(dm.dm_id))}
                      className={cn(
                        'flex w-full items-center gap-2 rounded px-3 py-1 text-[15px] hover:bg-slack-purple-hover transition-all duration-75',
                        activeDMId === dm.dm_id && 'bg-slack-purple-active text-white font-bold'
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
                        <span className="ml-auto rounded-full bg-slack-red px-1.5 py-0.5 text-xs font-bold">
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
        <div className="border-t border-slack-purple-border p-3">
          <div className="group relative">
            <button className="flex w-full items-center gap-2 rounded px-2 py-1.5 hover:bg-slack-purple-hover transition-all duration-75">
              <Avatar
                src={user.avatar_url}
                name={user.display_name}
                userId={user.user_id}
                size="md"
                status="online"
              />
              <div className="flex-1 text-left min-w-0">
                <p className="text-[15px] font-bold truncate">{user.display_name}</p>
                <p className="text-xs text-white/70 truncate">🟢 Active</p>
              </div>
            </button>

            {/* Logout button on hover */}
            <button
              onClick={handleLogout}
              className="absolute right-2 top-2 hidden rounded bg-slack-red p-1.5 text-white hover:bg-opacity-90 group-hover:block"
              title="Logout"
            >
              <LogOut className="h-3.5 w-3.5" />
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
        'flex w-full items-center gap-1.5 rounded px-3 py-1 text-[15px] font-normal hover:bg-slack-purple-hover transition-all duration-75',
        active && 'bg-slack-purple-active text-white font-bold'
      )}
    >
      <Icon className="h-[18px] w-[18px]" />
      <span className="truncate">{label}</span>
    </button>
  )
}
