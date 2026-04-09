'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { setStoredToken, setStoredUserId, getStoredToken } from '@/lib/hooks/useAuth'

export default function LoginPage() {
  const router = useRouter()
  const [userId, setUserId] = useState('')
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)

  useEffect(() => {
    // If already logged in, redirect to home
    if (getStoredToken()) {
      router.push('/')
      return
    }
    setIsCheckingAuth(false)
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    const trimmedUserId = userId.trim()
    const trimmedEmail = email.trim() || `${trimmedUserId}@example.com`

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/token`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: trimmedUserId, email: trimmedEmail }),
        }
      )

      if (!response.ok) {
        throw new Error('Login failed')
      }

      const data = await response.json()
      setStoredToken(data.access_token)
      setStoredUserId(trimmedUserId)

      router.push('/')
    } catch (err) {
      setError('Login failed. Please check your credentials.')
      setIsLoading(false)
    }
  }

  if (isCheckingAuth) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: 'var(--background)' }}
      >
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--primary)' }} />
      </div>
    )
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ backgroundColor: 'var(--background)' }}
    >
      <div
        className="w-full max-w-md rounded-2xl border p-8"
        style={{
          backgroundColor: 'var(--card)',
          borderColor: 'var(--border)',
        }}
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div
            className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center mb-4"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="1.5"
              className="w-8 h-8"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <h1
            className="text-2xl font-bold mb-2"
            style={{ color: 'var(--foreground)' }}
          >
            RAG Chatbot
          </h1>
          <p style={{ color: 'var(--muted)' }}>
            Sign in to your account
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label
              htmlFor="userId"
              className="block text-sm font-medium mb-2"
              style={{ color: 'var(--foreground)' }}
            >
              User ID
            </label>
            <input
              id="userId"
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Enter your user ID"
              required
              className="w-full px-4 py-3 rounded-xl border outline-none transition-all"
              style={{
                backgroundColor: 'var(--input)',
                borderColor: 'var(--border)',
                color: 'var(--foreground)',
              }}
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium mb-2"
              style={{ color: 'var(--foreground)' }}
            >
              Email (optional)
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              className="w-full px-4 py-3 rounded-xl border outline-none transition-all"
              style={{
                backgroundColor: 'var(--input)',
                borderColor: 'var(--border)',
                color: 'var(--foreground)',
              }}
            />
          </div>

          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}

          <button
            type="submit"
            disabled={isLoading || !userId.trim()}
            className="w-full py-3 rounded-xl font-medium text-white transition-all disabled:opacity-50"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin mx-auto" />
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Demo hint */}
        <p
          className="mt-6 text-center text-sm"
          style={{ color: 'var(--muted-foreground)' }}
        >
          Use any user ID to sign in. New accounts are created automatically.
        </p>
      </div>
    </div>
  )
}