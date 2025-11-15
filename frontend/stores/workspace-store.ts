import { create } from 'zustand'
import { Workspace, Channel, DirectMessage } from '@/types'

interface WorkspaceState {
  currentWorkspace: Workspace | null
  channels: Channel[]
  directMessages: DirectMessage[]
  activeChannelId: string | null
  activeDMId: string | null
  setCurrentWorkspace: (workspace: Workspace | null) => void
  setChannels: (channels: Channel[]) => void
  setDirectMessages: (dms: DirectMessage[]) => void
  setActiveChannel: (channelId: string) => void
  setActiveDM: (dmId: string) => void
  addChannel: (channel: Channel) => void
  updateChannel: (channelId: string, updates: Partial<Channel>) => void
  clearActive: () => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  currentWorkspace: null,
  channels: [],
  directMessages: [],
  activeChannelId: null,
  activeDMId: null,
  setCurrentWorkspace: (workspace) => set({ currentWorkspace: workspace }),
  setChannels: (channels) => set({ channels }),
  setDirectMessages: (dms) => set({ directMessages: dms }),
  setActiveChannel: (channelId) => set({ activeChannelId: channelId, activeDMId: null }),
  setActiveDM: (dmId) => set({ activeDMId: dmId, activeChannelId: null }),
  addChannel: (channel) => set((state) => ({ channels: [...state.channels, channel] })),
  updateChannel: (channelId, updates) =>
    set((state) => ({
      channels: state.channels.map((ch) =>
        ch.channel_id === channelId ? { ...ch, ...updates } : ch
      ),
    })),
  clearActive: () => set({ activeChannelId: null, activeDMId: null }),
}))
