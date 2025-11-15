import React from 'react'
import { cn, getInitials, getAvatarColor } from '@/lib/utils'

interface AvatarProps {
  src?: string
  name: string
  userId: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  status?: 'online' | 'away' | 'offline'
  className?: string
}

const sizeClasses = {
  sm: 'h-6 w-6 text-xs',
  md: 'h-8 w-8 text-sm',
  lg: 'h-10 w-10 text-base',
  xl: 'h-16 w-16 text-2xl',
}

const statusClasses = {
  online: 'bg-green-500',
  away: 'bg-yellow-500',
  offline: 'bg-gray-400',
}

export function Avatar({ src, name, userId, size = 'md', status, className }: AvatarProps) {
  const initials = getInitials(name)
  const colorClass = getAvatarColor(userId)

  return (
    <div className={cn('relative inline-block', className)}>
      <div
        className={cn(
          'flex items-center justify-center rounded font-semibold text-white',
          sizeClasses[size],
          !src && colorClass
        )}
      >
        {src ? (
          <img src={src} alt={name} className="h-full w-full rounded object-cover" />
        ) : (
          initials
        )}
      </div>
      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 block h-2 w-2 rounded-full ring-2 ring-white',
            statusClasses[status],
            size === 'sm' && 'h-1.5 w-1.5',
            size === 'xl' && 'h-3 w-3'
          )}
        />
      )}
    </div>
  )
}
