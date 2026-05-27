'use client'

import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ForgotPasswordPage() {
  const [email, setEmail]       = useState('')
  const [sent, setSent]         = useState(false)
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    await fetch(`${API_URL}/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    setSent(true)
    setLoading(false)
  }

  return (
    <main style={{
      backgroundColor: '#f5f4f0',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'sans-serif',
    }}>
      <div style={{ maxWidth: '480px', width: '100%', padding: '48px' }}>

        <a href="/auth" style={{ fontSize: '12px', color: '#999', textDecoration: 'none', letterSpacing: '0.06em', display: 'block', marginBottom: '48px' }}>
          ← back to sign in
        </a>

        <h1 style={{ fontFamily: 'Georgia, serif', fontSize: '28px', fontWeight: '400', color: '#1a1a1a', marginBottom: '12px' }}>
          forgot your password?
        </h1>

        {sent ? (
          <p style={{ fontSize: '14px', color: '#888', lineHeight: '1.7' }}>
            if that email is in our system, you'll get a reset link shortly. check your inbox.
          </p>
        ) : (
          <>
            <p style={{ fontSize: '14px', color: '#888', lineHeight: '1.7', marginBottom: '36px' }}>
              enter your email and we'll send you a link to reset it.
            </p>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <label style={{ fontSize: '11px', color: '#999', letterSpacing: '0.08em', display: 'block', marginBottom: '8px' }}>email</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                  style={{
                    width: '100%', border: 'none', borderBottom: '1px solid #ddd',
                    background: 'transparent', padding: '10px 0', fontSize: '14px',
                    fontFamily: 'sans-serif', outline: 'none', color: '#1a1a1a',
                  }}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                style={{
                  background: loading ? '#999' : '#1a1a1a', color: '#f5f4f0',
                  border: 'none', padding: '14px', fontSize: '13px',
                  letterSpacing: '0.04em', cursor: loading ? 'not-allowed' : 'pointer',
                }}
              >
                {loading ? 'sending...' : 'send reset link'}
              </button>
            </form>
          </>
        )}
      </div>
    </main>
  )
}
