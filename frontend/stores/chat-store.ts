import { create } from 'zustand'
import { Message, TypingIndicator } from '@/types'

interface ChatState {
  messages: Record<string, Message[]>
  typingUsers: TypingIndicator[]
  threadMessageId: string | null
  threadMessages: Message[]
  setMessages: (channelId: string, messages: Message[]) => void
  addMessage: (channelId: string, message: Message) => void
  updateMessage: (channelId: string, messageId: string, updates: Partial<Message>) => void
  deleteMessage: (channelId: string, messageId: string) => void
  setTypingUsers: (users: TypingIndicator[]) => void
  addTypingUser: (user: TypingIndicator) => void
  removeTypingUser: (userId: string) => void
  setThread: (messageId: string | null) => void
  setThreadMessages: (messages: Message[]) => void
  addThreadMessage: (message: Message) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: {},
  typingUsers: [],
  threadMessageId: null,
  threadMessages: [],
  setMessages: (channelId, messages) =>
    set((state) => ({
      messages: { ...state.messages, [channelId]: messages },
    })),
  addMessage: (channelId, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [channelId]: [...(state.messages[channelId] || []), message],
      },
    })),
  updateMessage: (channelId, messageId, updates) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [channelId]: state.messages[channelId]?.map((msg) =>
          msg.message_id === messageId ? { ...msg, ...updates } : msg
        ) || [],
      },
    })),
  deleteMessage: (channelId, messageId) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [channelId]: state.messages[channelId]?.map((msg) =>
          msg.message_id === messageId ? { ...msg, is_deleted: true } : msg
        ) || [],
      },
    })),
  setTypingUsers: (users) => set({ typingUsers: users }),
  addTypingUser: (user) =>
    set((state) => {
      const exists = state.typingUsers.find((u) => u.user_id === user.user_id)
      if (exists) return state
      return { typingUsers: [...state.typingUsers, user] }
    }),
  removeTypingUser: (userId) =>
    set((state) => ({
      typingUsers: state.typingUsers.filter((u) => u.user_id !== userId),
    })),
  setThread: (messageId) => set({ threadMessageId: messageId, threadMessages: [] }),
  setThreadMessages: (messages) => set({ threadMessages: messages }),
  addThreadMessage: (message) =>
    set((state) => ({ threadMessages: [...state.threadMessages, message] })),
}))
