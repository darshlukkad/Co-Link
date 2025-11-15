'use client'

import { useState } from 'react'
import { X, Mail, Calendar, Clock, Edit2 } from 'lucide-react'
import { User } from '@/types'
import { Avatar } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiClient } from '@/lib/api-client'
import { formatMessageTime } from '@/lib/utils'

interface UserProfileModalProps {
  isOpen: boolean
  onClose: () => void
  user: User
  isCurrentUser?: boolean
  onUpdate?: (user: User) => void
}

export function UserProfileModal({
  isOpen,
  onClose,
  user,
  isCurrentUser = false,
  onUpdate,
}: UserProfileModalProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [displayName, setDisplayName] = useState(user.display_name)
  const [bio, setBio] = useState(user.bio || '')
  const [timezone, setTimezone] = useState(user.timezone || '')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    setError(null)
    setIsLoading(true)

    try {
      // @ts-expect-error - updateUser method needs to be added to ApiClient type definition
      const updated = await apiClient.updateUser(user.user_id, {
        display_name: displayName,
        bio,
        timezone,
      })

      if (onUpdate) {
        onUpdate(updated)
      }

      setIsEditing(false)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update profile')
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg rounded-lg bg-white shadow-2xl">
        {/* Header with gradient background */}
        <div className="relative h-24 rounded-t-lg bg-gradient-to-r from-[#007a5a] to-[#005a42]">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 rounded bg-black bg-opacity-20 p-1 text-white hover:bg-opacity-30"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Avatar */}
        <div className="relative px-6">
          <div className="absolute -top-12">
            <Avatar
              src={user.avatar_url}
              name={user.display_name}
              userId={user.user_id}
              size="xl"
              status={user.is_active ? 'online' : 'offline'}
              className="ring-4 ring-white"
            />
          </div>
        </div>

        {/* Content */}
        <div className="px-6 pb-6 pt-16">
          {isEditing ? (
            <div className="space-y-4">
              <Input
                label="Display Name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
              />

              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Bio
                </label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Tell us about yourself..."
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-[#007a5a] focus:outline-none focus:ring-1 focus:ring-[#007a5a]"
                  rows={3}
                />
              </div>

              <Input
                label="Timezone"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                placeholder="e.g., America/New_York"
              />

              {error && (
                <div className="rounded bg-red-50 p-3 text-sm text-red-600">
                  {error}
                </div>
              )}

              <div className="flex justify-end space-x-2">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setIsEditing(false)
                    setDisplayName(user.display_name)
                    setBio(user.bio || '')
                    setTimezone(user.timezone || '')
                  }}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSave}
                  disabled={isLoading || !displayName.trim()}
                >
                  {isLoading ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {user.display_name}
                  </h2>
                  <p className="text-sm text-gray-500">@{user.username}</p>
                </div>
                {isCurrentUser && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                  >
                    <Edit2 className="mr-1 h-4 w-4" />
                    Edit
                  </Button>
                )}
              </div>

              {user.bio && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700">About</h3>
                  <p className="mt-1 text-sm text-gray-600">{user.bio}</p>
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center space-x-2 text-sm">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <span className="text-gray-600">{user.email}</span>
                </div>

                {user.timezone && (
                  <div className="flex items-center space-x-2 text-sm">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600">{user.timezone}</span>
                  </div>
                )}

                <div className="flex items-center space-x-2 text-sm">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span className="text-gray-600">
                    Joined {new Date(user.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {!isCurrentUser && (
                <div className="flex space-x-2 pt-4">
                  <Button variant="primary" className="flex-1">
                    Send Message
                  </Button>
                  <Button variant="secondary" className="flex-1">
                    View Profile
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
