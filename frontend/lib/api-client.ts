import { Channel, DirectMessage, Message, User, SearchResult } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const TOKEN_KEY = 'colink_auth_token'
const REFRESH_TOKEN_KEY = 'colink_refresh_token'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  /**
   * Get stored auth token
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEY)
  }

  /**
   * Set auth token
   */
  setToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(TOKEN_KEY, token)
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  /**
   * Set refresh token
   */
  setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  }

  /**
   * Clear all tokens
   */
  clearTokens(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  /**
   * Make authenticated request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      // Token expired, try to refresh
      const refreshed = await this.refreshToken()
      if (refreshed) {
        // Retry the request with new token
        return this.request(endpoint, options)
      } else {
        // Refresh failed, clear tokens and redirect to login
        this.clearTokens()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        throw new Error('Authentication failed')
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }))
      throw new Error(error.message || `Request failed: ${response.status}`)
    }

    return response.json()
  }

  /**
   * Auth: Login with email/password
   */
  async login(email: string, password: string): Promise<{ token: string; refresh_token: string; user: User }> {
    const data = await this.request<{ token: string; refresh_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })

    this.setToken(data.token)
    this.setRefreshToken(data.refresh_token)
    return data
  }

  /**
   * Auth: Login with SSO (Google/GitHub)
   */
  async loginWithSSO(provider: 'google' | 'github', code: string): Promise<{ token: string; refresh_token: string; user: User }> {
    const data = await this.request<{ token: string; refresh_token: string; user: User }>(`/auth/sso/${provider}`, {
      method: 'POST',
      body: JSON.stringify({ code }),
    })

    this.setToken(data.token)
    this.setRefreshToken(data.refresh_token)
    return data
  }

  /**
   * Auth: Refresh token
   */
  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = this.getRefreshToken()
      if (!refreshToken) return false

      const data = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).then(res => res.json())

      if (data.token) {
        this.setToken(data.token)
        if (data.refresh_token) {
          this.setRefreshToken(data.refresh_token)
        }
        return true
      }

      return false
    } catch (error) {
      console.error('Token refresh failed:', error)
      return false
    }
  }

  /**
   * Auth: Logout
   */
  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' })
    } catch (error) {
      console.error('Logout request failed:', error)
    } finally {
      this.clearTokens()
    }
  }

  /**
   * Auth: Get current user
   */
  async getMe(): Promise<User> {
    return this.request<User>('/users/me')
  }

  /**
   * Users: Get user by ID
   */
  async getUser(userId: string): Promise<User> {
    return this.request<User>(`/users/${userId}`)
  }

  /**
   * Users: Update user profile
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    return this.request<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  /**
   * Users: Set online status
   */
  async setOnline(online: boolean): Promise<void> {
    await this.request('/presence/status', {
      method: 'POST',
      body: JSON.stringify({ status: online ? 'online' : 'away' }),
    })
  }

  /**
   * Channels: Get all channels in workspace
   */
  async getChannels(workspaceId: string): Promise<Channel[]> {
    return this.request<Channel[]>(`/channels?workspace_id=${workspaceId}`)
  }

  /**
   * Channels: Get channel by ID
   */
  async getChannel(channelId: string): Promise<Channel> {
    return this.request<Channel>(`/channels/${channelId}`)
  }

  /**
   * Channels: Create new channel
   */
  async createChannel(data: { workspace_id: string; name: string; description?: string; is_private?: boolean }): Promise<Channel> {
    return this.request<Channel>('/channels', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * Channels: Join channel
   */
  async joinChannel(channelId: string): Promise<void> {
    await this.request(`/channels/${channelId}/join`, { method: 'POST' })
  }

  /**
   * Channels: Leave channel
   */
  async leaveChannel(channelId: string): Promise<void> {
    await this.request(`/channels/${channelId}/leave`, { method: 'POST' })
  }

  /**
   * Direct Messages: Get all DMs in workspace
   */
  async getDMs(workspaceId: string): Promise<DirectMessage[]> {
    return this.request<DirectMessage[]>(`/dms?workspace_id=${workspaceId}`)
  }

  /**
   * Direct Messages: Create or get DM with user
   */
  async createDM(workspaceId: string, userId: string): Promise<DirectMessage> {
    return this.request<DirectMessage>('/dms', {
      method: 'POST',
      body: JSON.stringify({
        workspace_id: workspaceId,
        user_id: userId,
      }),
    })
  }

  /**
   * Messages: Get messages in channel
   */
  async getMessages(channelId: string, limit: number = 50, offset: number = 0): Promise<Message[]> {
    return this.request<Message[]>(`/messages?channel_id=${channelId}&limit=${limit}&offset=${offset}`)
  }

  /**
   * Messages: Send message
   */
  async sendMessage(channelId: string, content: string, dmId?: string): Promise<Message> {
    return this.request<Message>('/messages', {
      method: 'POST',
      body: JSON.stringify({
        channel_id: channelId || undefined,
        dm_id: dmId || undefined,
        content,
      }),
    })
  }

  /**
   * Messages: Update message
   */
  async updateMessage(messageId: string, content: string): Promise<Message> {
    return this.request<Message>(`/messages/${messageId}`, {
      method: 'PATCH',
      body: JSON.stringify({ content }),
    })
  }

  /**
   * Messages: Delete message
   */
  async deleteMessage(messageId: string): Promise<void> {
    await this.request(`/messages/${messageId}`, { method: 'DELETE' })
  }

  /**
   * Reactions: Add reaction to message
   */
  async addReaction(messageId: string, emoji: string): Promise<void> {
    await this.request(`/messages/${messageId}/reactions`, {
      method: 'POST',
      body: JSON.stringify({ emoji }),
    })
  }

  /**
   * Reactions: Remove reaction from message
   */
  async removeReaction(messageId: string, emoji: string): Promise<void> {
    await this.request(`/messages/${messageId}/reactions`, {
      method: 'DELETE',
      body: JSON.stringify({ emoji }),
    })
  }

  /**
   * Threads: Get thread messages (alias for getThreadMessages)
   */
  async getThreadMessages(messageId: string): Promise<Message[]> {
    return this.request<Message[]>(`/messages/${messageId}/thread`)
  }

  /**
   * Threads: Get thread replies (alias for getThreadMessages)
   */
  async getThreadReplies(messageId: string): Promise<Message[]> {
    return this.getThreadMessages(messageId)
  }

  /**
   * Threads: Reply to thread
   */
  async replyToThread(messageId: string, content: string): Promise<Message> {
    return this.request<Message>(`/messages/${messageId}/thread`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    })
  }

  /**
   * Threads: Send thread reply (alias for replyToThread)
   */
  async sendThreadReply(messageId: string, content: string): Promise<Message> {
    return this.replyToThread(messageId, content)
  }

  /**
   * Typing: Send typing indicator
   */
  async startTyping(channelId: string): Promise<void> {
    await this.request('/presence/typing', {
      method: 'POST',
      body: JSON.stringify({
        channel_id: channelId,
        typing: true,
      }),
    }).catch(() => {}) // Ignore errors for typing indicators
  }

  /**
   * Typing: Stop typing indicator
   */
  async stopTyping(channelId: string): Promise<void> {
    await this.request('/presence/typing', {
      method: 'POST',
      body: JSON.stringify({
        channel_id: channelId,
        typing: false,
      }),
    }).catch(() => {}) // Ignore errors for typing indicators
  }

  /**
   * Files: Upload file
   */
  async uploadFile(
    file: File,
    workspaceId: string,
    channelId?: string,
    dmId?: string
  ): Promise<{ file_id: string; url: string }> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('workspace_id', workspaceId)
    if (channelId) formData.append('channel_id', channelId)
    if (dmId) formData.append('dm_id', dmId)

    const token = this.getToken()
    const response = await fetch(`${this.baseUrl}/files/upload`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    })

    if (!response.ok) {
      throw new Error('File upload failed')
    }

    return response.json()
  }

  /**
   * Files: Get file metadata
   */
  async getFile(fileId: string): Promise<any> {
    return this.request(`/files/${fileId}`)
  }

  /**
   * Search: Search messages
   */
  async searchMessages(workspaceId: string, query: string, limit: number = 20): Promise<SearchResult[]> {
    return this.request<SearchResult[]>(
      `/search/messages?workspace_id=${workspaceId}&query=${encodeURIComponent(query)}&limit=${limit}`
    )
  }

  /**
   * Search: Search files
   */
  async searchFiles(workspaceId: string, query: string, limit: number = 20): Promise<any[]> {
    return this.request<any[]>(
      `/search/files?workspace_id=${workspaceId}&query=${encodeURIComponent(query)}&limit=${limit}`
    )
  }
}

export const apiClient = new ApiClient(API_BASE_URL)
