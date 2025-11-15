'use client'

import { useState } from 'react'
import { X, Hash, Lock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiClient } from '@/lib/api-client'

interface CreateChannelModalProps {
  isOpen: boolean
  onClose: () => void
  workspaceId: string
  onChannelCreated?: (channel: any) => void
}

export function CreateChannelModal({
  isOpen,
  onClose,
  workspaceId,
  onChannelCreated,
}: CreateChannelModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isPrivate, setIsPrivate] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const channel = await apiClient.createChannel({
        workspace_id: workspaceId,
        name: name.toLowerCase().replace(/\s+/g, '-'),
        description,
        is_private: isPrivate,
      })

      if (onChannelCreated) {
        onChannelCreated(channel)
      }

      // Reset and close
      setName('')
      setDescription('')
      setIsPrivate(false)
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create channel')
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
      <div className="relative z-10 w-full max-w-lg rounded-lg bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">Create a channel</h2>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-6 text-sm text-gray-600">
          Channels are where your team communicates. They're best when organized
          around a topic — #marketing, for example.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. marketing"
            required
            autoFocus
          />

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              Description <span className="text-gray-400">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this channel about?"
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-[#007a5a] focus:outline-none focus:ring-1 focus:ring-[#007a5a]"
              rows={3}
            />
          </div>

          <div>
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={isPrivate}
                onChange={(e) => setIsPrivate(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-[#007a5a] focus:ring-[#007a5a]"
              />
              <div className="flex items-center space-x-2">
                {isPrivate ? (
                  <Lock className="h-4 w-4 text-gray-600" />
                ) : (
                  <Hash className="h-4 w-4 text-gray-600" />
                )}
                <span className="text-sm font-medium">
                  Make private
                </span>
              </div>
            </label>
            <p className="ml-7 mt-1 text-xs text-gray-500">
              {isPrivate
                ? 'Only specific people can access this channel'
                : 'Anyone in your workspace can view and join'}
            </p>
          </div>

          {error && (
            <div className="rounded bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={!name.trim() || isLoading}
            >
              {isLoading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
