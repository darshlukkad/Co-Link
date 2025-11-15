'use client'

interface TypingIndicatorProps {
  userNames: string[]
}

export function TypingIndicator({ userNames }: TypingIndicatorProps) {
  if (userNames.length === 0) return null

  const getTypingText = () => {
    if (userNames.length === 1) {
      return `${userNames[0]} is typing...`
    } else if (userNames.length === 2) {
      return `${userNames[0]} and ${userNames[1]} are typing...`
    } else if (userNames.length === 3) {
      return `${userNames[0]}, ${userNames[1]}, and ${userNames[2]} are typing...`
    } else {
      return `${userNames.length} people are typing...`
    }
  }

  return (
    <div className="px-5 py-2 text-sm text-gray-600 animate-fadeIn">
      <div className="flex items-center space-x-2">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
        <span className="text-sm italic">{getTypingText()}</span>
      </div>
    </div>
  )
}
