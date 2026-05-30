'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function WaitingPage() {
  const router = useRouter()
  const [dots, setDots] = useState('.')

  useEffect(() => {
    const userId = localStorage.getItem('user_id')
    if (!userId) {
      router.push('/auth')
      return
    }

    // Animate the dots
    const dotInterval = setInterval(() => {
      setDots(d => d.length >= 3 ? '.' : d + '.')
    }, 500)

    // Poll every 3 seconds to check if briefing is ready
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/briefing-ready/${userId}`)
        const data = await res.json()
        if (data.ready) {
          clearInterval(pollInterval)
          clearInterval(dotInterval)
          router.push('/briefing')
        }
      } catch (e) {
        // keep polling
      }
    }, 3000)

    return () => {
      clearInterval(pollInterval)
      clearInterval(dotInterval)
    }
  }, [router])

  return (
    <main style={{
      backgroundColor: '#f5f4f0',
      minHeight: '100vh',
      fontFamily: 'Georgia, serif',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{ textAlign: 'center', maxWidth: '400px', padding: '0 24px' }}>

        <div style={{
          fontSize: '28px',
          marginBottom: '32px',
          opacity: 0.4,
        }}>
          ◎
        </div>

        <h1 style={{
          fontSize: '24px',
          fontWeight: '400',
          color: '#1a1a1a',
          marginBottom: '16px',
          letterSpacing: '-0.01em',
        }}>
          Building your briefing{dots}
        </h1>

        <p style={{
          fontSize: '14px',
          fontFamily: 'sans-serif',
          color: '#999',
          lineHeight: '1.7',
        }}>
          We're ranking and summarizing articles based on your interests.
          This takes about a minute.
        </p>

      </div>
    </main>
  )
}
