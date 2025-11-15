export interface User {
  user_id: string
  email: string
  username: string
  display_name: string
  avatar_url?: string
  bio?: string
  timezone?: string
  is_active: boolean
  created_at: string
}

export interface Workspace {
  workspace_id: string
  name: string
  icon_url?: string
  created_at: string
}

export interface Channel {
  channel_id: string
  workspace_id: string
  name: string
  description?: string
  topic?: string
  is_private: boolean
  is_archived: boolean
  created_by: string
  created_at: string
  member_count?: number
  unread_count?: number
}

export interface DirectMessage {
  dm_id: string
  workspace_id: string
  participant_user_ids: string[]
  created_at: string
  participants?: User[]
  unread_count?: number
  last_message?: Message
}

export interface Message {
  message_id: string
  channel_id?: string
  dm_id?: string
  user_id: string
  content: string
  message_type: 'text' | 'file' | 'system'
  parent_message_id?: string
  is_edited: boolean
  is_deleted: boolean
  created_at: string
  updated_at?: string
  user?: User
  reactions?: Reaction[]
  thread_reply_count?: number
  file_attachments?: FileAttachment[]
}

export interface Reaction {
  reaction_id: string
  message_id: string
  user_id: string
  emoji: string
  created_at: string
  user?: User
}

export interface FileAttachment {
  file_id: string
  filename: string
  content_type: string
  size_bytes: number
  url?: string
  thumbnail_url?: string
}

export interface ChannelMember {
  channel_id: string
  user_id: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
  user?: User
}

export interface PresenceStatus {
  user_id: string
  status: 'online' | 'away' | 'offline'
  last_seen_at?: string
}

export interface TypingIndicator {
  channel_id: string
  user_id: string
  user?: User
}

export interface SearchResult {
  messages: Message[]
  files: FileAttachment[]
  total_messages: number
  total_files: number
}

export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}
