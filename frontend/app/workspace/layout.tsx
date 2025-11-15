'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { apiClient } from '@/lib/api-client'
import { wsClient } from '@/lib/websocket-client'
import Sidebar from '@/components/sidebar/sidebar'

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const { user, isAuthenticated, isLoading, setUser } = useAuthStore()

  useEffect(() => {
    const checkAuth = async () => {
      const token = apiClient.getToken()
      if (!token) {
        router.push('/login')
        return
      }

      try {
        const userData = await apiClient.getMe()
        setUser(userData)

        // Connect WebSocket
        wsClient.connect(token)
        await apiClient.setOnline()
      } catch (error) {
        console.error('Auth check failed:', error)
        router.push('/login')
      }
    }

    if (!isAuthenticated && !isLoading) {
      checkAuth()
    }
  }, [isAuthenticated, isLoading, router, setUser])

  if (isLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-[#007a5a] mx-auto" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        {children}
      </div>
    </div>
  )
}
