'use client'

import { useState } from 'react'
import { ChevronDown, Plus, Settings, LogOut, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Workspace {
  id: string
  name: string
  icon?: string
  unreadCount?: number
}

interface WorkspaceSwitcherProps {
  currentWorkspace: Workspace
  workspaces?: Workspace[]
  onWorkspaceChange?: (workspaceId: string) => void
  onCreateWorkspace?: () => void
  onSettings?: () => void
  onSignOut?: () => void
}

export function WorkspaceSwitcher({
  currentWorkspace,
  workspaces = [],
  onWorkspaceChange,
  onCreateWorkspace,
  onSettings,
  onSignOut
}: WorkspaceSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false)

  const getWorkspaceInitial = (name: string) => {
    return name.charAt(0).toUpperCase()
  }

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between border-b border-slack-purple-border px-4 py-3.5 text-left hover:bg-slack-purple-hover transition-all duration-100"
      >
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded bg-white text-slack-purple font-black text-lg shadow-sm">
            {currentWorkspace.icon || getWorkspaceInitial(currentWorkspace.name)}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="font-black text-[15px] leading-tight truncate text-white">
              {currentWorkspace.name}
            </h2>
            {currentWorkspace.unreadCount && currentWorkspace.unreadCount > 0 && (
              <div className="flex items-center mt-0.5">
                <span className="inline-flex items-center rounded-full bg-white px-2 py-0.5 text-xs font-bold text-slack-purple">
                  {currentWorkspace.unreadCount} unread
                </span>
              </div>
            )}
          </div>
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 opacity-70 transition-transform duration-200",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute left-4 right-4 top-full z-50 mt-1 rounded-lg border border-gray-200 bg-white shadow-2xl animate-scale-in overflow-hidden">
            {/* Current Workspace */}
            <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2.5 px-2 py-1.5">
                <div className="flex h-8 w-8 items-center justify-center rounded bg-slack-purple text-white font-black text-sm">
                  {currentWorkspace.icon || getWorkspaceInitial(currentWorkspace.name)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-sm text-gray-900 truncate">
                    {currentWorkspace.name}
                  </div>
                  <div className="text-xs text-gray-500">Current workspace</div>
                </div>
                <Check className="h-4 w-4 text-green-600" />
              </div>
            </div>

            {/* Other Workspaces */}
            {workspaces.length > 0 && (
              <div className="py-1 border-b border-gray-200">
                <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 uppercase">
                  Switch to
                </div>
                {workspaces.map((workspace) => (
                  <button
                    key={workspace.id}
                    onClick={() => {
                      onWorkspaceChange?.(workspace.id)
                      setIsOpen(false)
                    }}
                    className="flex w-full items-center gap-2.5 px-5 py-2 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded bg-gray-200 text-gray-700 font-bold text-sm">
                      {workspace.icon || getWorkspaceInitial(workspace.name)}
                    </div>
                    <div className="flex-1 text-left min-w-0">
                      <div className="font-medium text-sm text-gray-900 truncate">
                        {workspace.name}
                      </div>
                    </div>
                    {workspace.unreadCount && workspace.unreadCount > 0 && (
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
                        {workspace.unreadCount > 9 ? '9+' : workspace.unreadCount}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="py-1">
              {onCreateWorkspace && (
                <button
                  onClick={() => {
                    onCreateWorkspace()
                    setIsOpen(false)
                  }}
                  className="flex w-full items-center gap-2.5 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  <span>Create a workspace</span>
                </button>
              )}
              {onSettings && (
                <button
                  onClick={() => {
                    onSettings()
                    setIsOpen(false)
                  }}
                  className="flex w-full items-center gap-2.5 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Settings className="h-4 w-4" />
                  <span>Workspace settings</span>
                </button>
              )}
            </div>

            {/* Sign Out */}
            {onSignOut && (
              <div className="border-t border-gray-200 py-1">
                <button
                  onClick={() => {
                    onSignOut()
                    setIsOpen(false)
                  }}
                  className="flex w-full items-center gap-2.5 px-5 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign out of CoLink</span>
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
