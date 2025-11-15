import { io, Socket } from 'socket.io-client'
import { Message } from '@/types'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8007'

type MessageCallback = (message: Message) => void
type MessageUpdatedCallback = (message: Partial<Message> & { message_id: string }) => void
type MessageDeletedCallback = (data: { message_id: string; channel_id?: string; dm_id?: string }) => void
type TypingCallback = (data: { user_id: string; channel_id: string; typing: boolean }) => void
type PresenceCallback = (data: { user_id: string; status: string }) => void
type ReactionCallback = (data: { message_id: string; user_id: string; emoji: string; action: 'add' | 'remove' }) => void

class WebSocketClient {
  private socket: Socket | null = null
  private url: string
  private messageCallbacks: MessageCallback[] = []
  private messageUpdatedCallbacks: MessageUpdatedCallback[] = []
  private messageDeletedCallbacks: MessageDeletedCallback[] = []
  private typingCallbacks: TypingCallback[] = []
  private presenceCallbacks: PresenceCallback[] = []
  private reactionCallbacks: ReactionCallback[] = []
  private isConnected: boolean = false
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 5

  constructor(url: string) {
    this.url = url
  }

  /**
   * Connect to WebSocket server
   */
  connect(token: string): void {
    if (this.socket && this.isConnected) {
      console.warn('WebSocket already connected')
      return
    }

    this.socket = io(this.url, {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    })

    this.setupEventListeners()
  }

  /**
   * Set up event listeners
   */
  private setupEventListeners(): void {
    if (!this.socket) return

    // Connection events
    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.isConnected = true
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      this.isConnected = false
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.reconnectAttempts++

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached')
        this.disconnect()
      }
    })

    // Message events
    this.socket.on('message:new', (message: Message) => {
      this.messageCallbacks.forEach(callback => callback(message))
    })

    this.socket.on('message:updated', (data: Partial<Message> & { message_id: string }) => {
      this.messageUpdatedCallbacks.forEach(callback => callback(data))
    })

    this.socket.on('message:deleted', (data: { message_id: string; channel_id?: string; dm_id?: string }) => {
      this.messageDeletedCallbacks.forEach(callback => callback(data))
    })

    // Reaction events
    this.socket.on('reaction:added', (data: { message_id: string; user_id: string; emoji: string }) => {
      this.reactionCallbacks.forEach(callback => callback({ ...data, action: 'add' }))
    })

    this.socket.on('reaction:removed', (data: { message_id: string; user_id: string; emoji: string }) => {
      this.reactionCallbacks.forEach(callback => callback({ ...data, action: 'remove' }))
    })

    // Typing events
    this.socket.on('typing:start', (data: { user_id: string; channel_id: string }) => {
      this.typingCallbacks.forEach(callback => callback({ ...data, typing: true }))
    })

    this.socket.on('typing:stop', (data: { user_id: string; channel_id: string }) => {
      this.typingCallbacks.forEach(callback => callback({ ...data, typing: false }))
    })

    // Presence events
    this.socket.on('presence:update', (data: { user_id: string; status: string }) => {
      this.presenceCallbacks.forEach(callback => callback(data))
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.isConnected = false
    }
  }

  /**
   * Check if connected
   */
  get connected(): boolean {
    return this.isConnected
  }

  /**
   * Join a channel (subscribe to channel events)
   */
  joinChannel(channelId: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('channel:join', { channel_id: channelId })
    }
  }

  /**
   * Leave a channel (unsubscribe from channel events)
   */
  leaveChannel(channelId: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('channel:leave', { channel_id: channelId })
    }
  }

  /**
   * Join a DM (subscribe to DM events)
   */
  joinDM(dmId: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('dm:join', { dm_id: dmId })
    }
  }

  /**
   * Leave a DM (unsubscribe from DM events)
   */
  leaveDM(dmId: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('dm:leave', { dm_id: dmId })
    }
  }

  /**
   * Register callback for new messages
   */
  onMessage(callback: MessageCallback): void {
    this.messageCallbacks.push(callback)
  }

  /**
   * Unregister callback for new messages
   */
  offMessage(callback: MessageCallback): void {
    this.messageCallbacks = this.messageCallbacks.filter(cb => cb !== callback)
  }

  /**
   * Register callback for message updates
   */
  onMessageUpdated(callback: MessageUpdatedCallback): void {
    this.messageUpdatedCallbacks.push(callback)
  }

  /**
   * Unregister callback for message updates
   */
  offMessageUpdated(callback: MessageUpdatedCallback): void {
    this.messageUpdatedCallbacks = this.messageUpdatedCallbacks.filter(cb => cb !== callback)
  }

  /**
   * Register callback for message deletions
   */
  onMessageDeleted(callback: MessageDeletedCallback): void {
    this.messageDeletedCallbacks.push(callback)
  }

  /**
   * Unregister callback for message deletions
   */
  offMessageDeleted(callback: MessageDeletedCallback): void {
    this.messageDeletedCallbacks = this.messageDeletedCallbacks.filter(cb => cb !== callback)
  }

  /**
   * Register callback for typing indicators
   */
  onTyping(callback: TypingCallback): void {
    this.typingCallbacks.push(callback)
  }

  /**
   * Unregister callback for typing indicators
   */
  offTyping(callback: TypingCallback): void {
    this.typingCallbacks = this.typingCallbacks.filter(cb => cb !== callback)
  }

  /**
   * Register callback for presence updates
   */
  onPresence(callback: PresenceCallback): void {
    this.presenceCallbacks.push(callback)
  }

  /**
   * Unregister callback for presence updates
   */
  offPresence(callback: PresenceCallback): void {
    this.presenceCallbacks = this.presenceCallbacks.filter(cb => cb !== callback)
  }

  /**
   * Register callback for reaction events
   */
  onReaction(callback: ReactionCallback): void {
    this.reactionCallbacks.push(callback)
  }

  /**
   * Unregister callback for reaction events
   */
  offReaction(callback: ReactionCallback): void {
    this.reactionCallbacks = this.reactionCallbacks.filter(cb => cb !== callback)
  }

  /**
   * Send custom event
   */
  emit(event: string, data: any): void {
    if (this.socket && this.isConnected) {
      this.socket.emit(event, data)
    }
  }

  /**
   * Listen for custom event
   */
  on(event: string, callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on(event, callback)
    }
  }

  /**
   * Stop listening for custom event
   */
  off(event: string, callback?: (data: any) => void): void {
    if (this.socket) {
      this.socket.off(event, callback)
    }
  }
}

export const wsClient = new WebSocketClient(WS_URL)
