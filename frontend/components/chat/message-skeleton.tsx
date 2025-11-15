'use client'

export function MessageSkeleton() {
  return (
    <div className="px-5 py-4 animate-pulse">
      <div className="flex space-x-3">
        {/* Avatar skeleton */}
        <div className="flex-shrink-0">
          <div className="h-9 w-9 rounded bg-gray-200" />
        </div>
        {/* Content skeleton */}
        <div className="flex-1 space-y-2">
          <div className="flex items-center space-x-2">
            <div className="h-4 w-24 rounded bg-gray-200" />
            <div className="h-3 w-16 rounded bg-gray-200" />
          </div>
          <div className="space-y-1.5">
            <div className="h-4 w-full rounded bg-gray-200" />
            <div className="h-4 w-4/5 rounded bg-gray-200" />
          </div>
        </div>
      </div>
    </div>
  )
}

export function MessageListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <MessageSkeleton key={i} />
      ))}
    </>
  )
}
