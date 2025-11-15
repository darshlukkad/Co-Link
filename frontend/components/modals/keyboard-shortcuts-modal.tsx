'use client'

import { X, Command } from 'lucide-react'
import { useEffect } from 'react'

interface KeyboardShortcutsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const shortcuts = [
    {
      category: 'Navigation',
      items: [
        { key: 'Cmd + K', description: 'Quick search' },
        { key: 'Cmd + /', description: 'Show keyboard shortcuts' },
        { key: 'Alt + ↑/↓', description: 'Previous/Next channel' },
        { key: 'Alt + Shift + ↑/↓', description: 'Previous/Next unread channel' },
      ]
    },
    {
      category: 'Messaging',
      items: [
        { key: 'Enter', description: 'Send message' },
        { key: 'Shift + Enter', description: 'New line in message' },
        { key: 'Cmd + B', description: 'Bold text' },
        { key: 'Cmd + I', description: 'Italic text' },
        { key: 'Cmd + Shift + X', description: 'Strike through text' },
        { key: '↑', description: 'Edit last message (in empty input)' },
      ]
    },
    {
      category: 'Actions',
      items: [
        { key: 'Cmd + U', description: 'Upload file' },
        { key: 'Cmd + Shift + A', description: 'View all unreads' },
        { key: 'Cmd + Shift + T', description: 'View all threads' },
        { key: 'Cmd + .', description: 'Toggle right sidebar' },
      ]
    },
    {
      category: 'Accessibility',
      items: [
        { key: 'Cmd + F', description: 'Search in current channel' },
        { key: 'Tab', description: 'Navigate through UI elements' },
        { key: 'Esc', description: 'Close modal or panel' },
      ]
    }
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-white rounded-lg shadow-xl overflow-hidden animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slack-purple">
              <Command className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Keyboard Shortcuts</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded p-2 hover:bg-gray-100 transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto px-6 py-6" style={{ maxHeight: 'calc(90vh - 80px)' }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {shortcuts.map((section) => (
              <div key={section.category}>
                <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-4">
                  {section.category}
                </h3>
                <div className="space-y-3">
                  {section.items.map((shortcut) => (
                    <div key={shortcut.key} className="flex items-start justify-between">
                      <span className="text-sm text-gray-900 flex-1">
                        {shortcut.description}
                      </span>
                      <kbd className="ml-4 inline-flex items-center rounded border border-gray-300 bg-gray-50 px-2 py-1 text-xs font-mono text-gray-800 whitespace-nowrap">
                        {shortcut.key}
                      </kbd>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">Tip:</span> Most shortcuts use <kbd className="inline-flex items-center rounded border border-gray-300 bg-white px-1.5 py-0.5 text-xs font-mono">Cmd</kbd> on Mac
              or <kbd className="inline-flex items-center rounded border border-gray-300 bg-white px-1.5 py-0.5 text-xs font-mono">Ctrl</kbd> on Windows/Linux.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
