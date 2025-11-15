'use client'

import { useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import { Smile } from 'lucide-react'
import { cn } from '@/lib/utils'

// Dynamically import emoji picker to avoid SSR issues
const Picker = dynamic(() => import('emoji-picker-react'), { ssr: false })

interface EmojiPickerProps {
  onEmojiSelect: (emoji: string) => void
  className?: string
}

export function EmojiPicker({ onEmojiSelect, className }: EmojiPickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const pickerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleEmojiClick = (emojiObject: any) => {
    onEmojiSelect(emojiObject.emoji)
    setIsOpen(false)
  }

  return (
    <div className={cn('relative', className)} ref={pickerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="rounded p-1 hover:bg-gray-100 transition-colors"
        title="Add emoji"
      >
        <Smile className="h-4 w-4 text-gray-600" />
      </button>

      {isOpen && (
        <div className="absolute bottom-full right-0 mb-2 z-50 shadow-2xl animate-scale-in">
          <Picker
            onEmojiClick={handleEmojiClick}
            width={320}
            height={400}
            previewConfig={{ showPreview: false }}
            searchPlaceHolder="Search emoji..."
            lazyLoadEmojis={true}
          />
        </div>
      )}
    </div>
  )
}
