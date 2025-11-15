import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { formatDistanceToNow, format, isToday, isYesterday } from 'date-fns'

/**
 * Merge Tailwind CSS classes with proper precedence
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format message timestamp in Slack-like format
 * - Just now (< 1 minute)
 * - X minutes ago (< 60 minutes)
 * - HH:MM AM/PM (today)
 * - Yesterday at HH:MM AM/PM
 * - Day at HH:MM AM/PM (< 7 days)
 * - MMM DD at HH:MM AM/PM (this year)
 * - MMM DD, YYYY at HH:MM AM/PM (older)
 */
export function formatMessageTime(timestamp: string | Date): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  // Just now (< 1 minute)
  if (diffInSeconds < 60) {
    return 'Just now'
  }

  // X minutes ago (< 60 minutes)
  if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`
  }

  // Today - show time only
  if (isToday(date)) {
    return format(date, 'h:mm a')
  }

  // Yesterday
  if (isYesterday(date)) {
    return `Yesterday at ${format(date, 'h:mm a')}`
  }

  // This week - show day and time
  const diffInDays = Math.floor(diffInSeconds / 86400)
  if (diffInDays < 7) {
    return format(date, 'EEEE \'at\' h:mm a')
  }

  // This year - show month, day, and time
  if (date.getFullYear() === now.getFullYear()) {
    return format(date, 'MMM d \'at\' h:mm a')
  }

  // Older - show full date and time
  return format(date, 'MMM d, yyyy \'at\' h:mm a')
}

/**
 * Get user initials from display name
 * e.g., "John Doe" => "JD"
 */
export function getInitials(name: string): string {
  if (!name || name.trim() === '') return '?'

  const parts = name.trim().split(/\s+/)

  if (parts.length === 1) {
    return parts[0].charAt(0).toUpperCase()
  }

  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase()
}

/**
 * Generate consistent avatar background color from user ID
 * Uses Slack's color palette for avatars
 */
export function getAvatarColor(userId: string): string {
  const colors = [
    '#e01e5a', // Red
    '#36c5f0', // Blue
    '#2eb67d', // Green
    '#ecb22e', // Yellow
    '#e8912d', // Orange
    '#4a154b', // Purple
    '#1264a3', // Dark Blue
    '#611f69', // Dark Purple
    '#205e73', // Teal
    '#d12d7e', // Pink
  ]

  // Generate a consistent hash from userId
  let hash = 0
  for (let i = 0; i < userId.length; i++) {
    hash = userId.charCodeAt(i) + ((hash << 5) - hash)
    hash = hash & hash // Convert to 32-bit integer
  }

  const index = Math.abs(hash) % colors.length
  return colors[index]
}

/**
 * Format file size in human-readable format
 * e.g., 1024 => "1 KB"
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * Check if a URL is an image
 */
export function isImageUrl(url: string): boolean {
  return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(url)
}

/**
 * Check if a URL is a video
 */
export function isVideoUrl(url: string): boolean {
  return /\.(mp4|webm|ogg|mov)$/i.test(url)
}

/**
 * Extract URLs from text
 */
export function extractUrls(text: string): string[] {
  const urlRegex = /(https?:\/\/[^\s]+)/g
  return text.match(urlRegex) || []
}

/**
 * Highlight mentions in text
 * e.g., "@john" => <span class="mention">@john</span>
 */
export function highlightMentions(text: string): string {
  return text.replace(/@(\w+)/g, '<span class="text-slack-blue font-medium bg-blue-50 px-1 rounded">@$1</span>')
}

/**
 * Parse markdown-style formatting to HTML
 * Supports: **bold**, *italic*, ~strikethrough~, `code`
 */
export function parseMarkdown(text: string): string {
  let result = text

  // Bold: **text** or __text__
  result = result.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>')
  result = result.replace(/__([^_]+)__/g, '<strong>$1</strong>')

  // Italic: *text* or _text_
  result = result.replace(/\*([^\*]+)\*/g, '<em>$1</em>')
  result = result.replace(/_([^_]+)_/g, '<em>$1</em>')

  // Strikethrough: ~text~
  result = result.replace(/~([^~]+)~/g, '<del>$1</del>')

  // Inline code: `text`
  result = result.replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-red-600 px-1 py-0.5 rounded text-sm">$1</code>')

  return result
}

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }

    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(later, wait)
  }
}

/**
 * Throttle function for performance optimization
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}
