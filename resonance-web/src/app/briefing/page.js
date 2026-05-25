'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function BriefingPage() {
  const router = useRouter()
  const [userName, setUserName] = useState('')

  useEffect(() => {
    const name = localStorage.getItem('user_name')
    const userId = localStorage.getItem('user_id')

    // If not logged in, redirect to auth
    if (!userId) {
      router.push('/auth')
      return
    }

    setUserName(name || '')
  }, [])

  return (
    <main style={{
      backgroundColor: '#f5f4f0',
      minHeight: '100vh',
      fontFamily: 'sans-serif',
      color: '#1a1a1a',
    }}>

      {/* Nav */}
      <nav style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '24px 48px',
        borderBottom: '1px solid #e8e6e0',
      }}>
        <span style={{
          fontFamily: 'Georgia, serif',
          fontSize: '15px',
          letterSpacing: '0.06em',
        }}>
          resonance
        </span>
        <div style={{ display: 'flex', gap: '24px', fontSize: '12px', color: '#999' }}>
          <a href="/briefing" style={{ textDecoration: 'none', color: '#1a1a1a' }}>briefing</a>
          <a href="/account" style={{ textDecoration: 'none', color: '#999' }}>account</a>
          <button
            onClick={() => {
              localStorage.removeItem('user_id')
              localStorage.removeItem('user_name')
              router.push('/')
            }}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '12px',
              color: '#999',
              cursor: 'pointer',
              padding: 0,
            }}
          >
            sign out
          </button>
        </div>
      </nav>

      {/* Page content */}
      <div style={{
        maxWidth: '640px',
        margin: '0 auto',
        padding: '80px 48px',
      }}>
        <div style={{
          fontSize: '11px',
          color: '#bbb',
          letterSpacing: '0.08em',
          marginBottom: '8px',
          fontFamily: 'sans-serif',
        }}>
          {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }).toLowerCase()}
        </div>

        <h1 style={{
          fontFamily: 'Georgia, serif',
          fontSize: '32px',
          fontWeight: '400',
          letterSpacing: '-0.01em',
          marginBottom: '64px',
          color: '#1a1a1a',
        }}>
          {userName ? `good morning, ${userName.split(' ')[0].toLowerCase()}.` : 'good morning.'}
        </h1>

        {/* Briefing content goes here */}
        <div style={{
          fontSize: '14px',
          color: '#bbb',
          fontFamily: 'sans-serif',
          lineHeight: '1.6',
        }}>
          your briefing is being prepared.
        </div>

      </div>
    </main>
  )
}