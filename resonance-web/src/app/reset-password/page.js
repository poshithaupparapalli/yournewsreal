'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function ResetForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [password, setPassword]     = useState('')
  const [confirm, setConfirm]       = useState('')
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState('')
  const [success, setSuccess]       = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (password !== confirm) { setError("passwords don't match"); return }
    if (password.length < 8)  { setError("password must be at least 8 characters"); return }

    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Something went wrong')
      setSuccess(true)
      setTimeout(() => router.push('/auth'), 2500)
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  if (!token) return (
    <p style={{ fontSize: '14px', color: '#888' }}>invalid reset link.</p>
  )

  if (success) return (
    <p style={{ fontSize: '14px', color: '#888', lineHeight: '1.7' }}>
      password updated. taking you to sign in...
    </p>
  )

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {error && (
        <div style={{ fontSize: '13px', color: '#c0392b', background: '#fdf0ef', padding: '12px', borderRadius: '2px' }}>
          {error}
        </div>
      )}
      <div>
        <label style={{ fontSize: '11px', color: '#999', letterSpacing: '0.08em', display: 'block', marginBottom: '8px' }}>new password</label>
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          minLength={8}
          placeholder="at least 8 characters"
          style={{
            width: '100%', border: 'none', borderBottom: '1px solid #ddd',
            background: 'transparent', padding: '10px 0', fontSize: '14px',
            fontFamily: 'sans-serif', outline: 'none', color: '#1a1a1a',
          }}
        />
      </div>
      <div>
        <label style={{ fontSize: '11px', color: '#999', letterSpacing: '0.08em', display: 'block', marginBottom: '8px' }}>confirm password</label>
        <input
          type="password"
          value={confirm}
          onChange={e => setConfirm(e.target.value)}
          required
          placeholder="same again"
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
        {loading ? 'updating...' : 'set new password'}
      </button>
    </form>
  )
}

export default function ResetPasswordPage() {
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
          set a new password.
        </h1>
        <p style={{ fontSize: '14px', color: '#888', lineHeight: '1.7', marginBottom: '36px' }}>
          choose something you'll remember.
        </p>
        <Suspense fallback={<div style={{ color: '#bbb', fontSize: '13px' }}>loading...</div>}>
          <ResetForm />
        </Suspense>
      </div>
    </main>
  )
}
