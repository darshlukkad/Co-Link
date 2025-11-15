'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api-client'

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    const token = apiClient.getToken()
    if (token) {
      router.push('/workspace')
    } else {
      router.push('/login')
    }
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-[#007a5a]" />
    </div>
  )
}
