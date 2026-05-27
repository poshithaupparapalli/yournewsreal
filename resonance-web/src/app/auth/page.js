'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || '${API_URL}'

const inputStyle = {
  width: '100%',
  border: 'none',
  borderBottom: '1px solid #ddd',
  background: 'transparent',
  padding: '10px 0',
  fontSize: '14px',
  fontFamily: 'sans-serif',
  outline: 'none',
  color: '#1a1a1a',
}

const labelStyle = {
  fontSize: '11px',
  color: '#999',
  letterSpacing: '0.08em',
  display: 'block',
  marginBottom: '8px',
}

export default function AuthPage() {
  const router = useRouter()
  const [mode, setMode] = useState('signup')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Form state
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [interests, setInterests] = useState('')
  const [learningGoals, setLearningGoals] = useState('')

  const isSignup = mode === 'signup'

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isSignup) {
        const res = await fetch(`${API_URL}/onboarding`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name,
            email,
            password,
            interests,
            learning_goals: learningGoals,
          }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Signup failed')

        // Store user_id in localStorage so briefing page knows who's logged in
        localStorage.setItem('user_id', data.user_id)
        localStorage.setItem('user_name', name)
        router.push('/briefing')

      } else {
        const res = await fetch(`${API_URL}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Login failed')

        localStorage.setItem('user_id', data.user_id)
        localStorage.setItem('user_name', data.name)
        router.push('/briefing')
      }

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{
      backgroundColor: '#f5f4f0',
      minHeight: '100vh',
      fontFamily: 'sans-serif',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{ maxWidth: '520px', width: '100%', padding: '48px' }}>

        <a href="/" style={{
          fontSize: '12px',
          color: '#999',
          textDecoration: 'none',
          letterSpacing: '0.06em',
          display: 'block',
          marginBottom: '48px',
        }}>
          ← resonance
        </a>

        <h1 style={{
          fontFamily: 'Georgia, serif',
          fontSize: '32px',
          fontWeight: '400',
          letterSpacing: '-0.01em',
          marginBottom: '8px',
          color: '#1a1a1a',
        }}>
          {isSignup ? 'tell us about you.' : 'welcome back.'}
        </h1>
        <p style={{
          fontSize: '14px',
          color: '#888',
          lineHeight: '1.6',
          marginBottom: '40px',
        }}>
          {isSignup
            ? 'your answers shape every briefing you receive.'
            : 'sign in to your resonance account.'}
        </p>

        {/* Toggle */}
        <div style={{
          display: 'flex',
          marginBottom: '40px',
          borderBottom: '1px solid #e8e6e0',
        }}>
          {['signup', 'login'].map(m => (
            <button
              key={m}
              onClick={() => { setMode(m); setError('') }}
              style={{
                background: 'none',
                border: 'none',
                padding: '10px 0',
                marginRight: '32px',
                fontSize: '13px',
                fontFamily: 'sans-serif',
                color: mode === m ? '#1a1a1a' : '#bbb',
                cursor: 'pointer',
                borderBottom: mode === m ? '1px solid #1a1a1a' : '1px solid transparent',
                marginBottom: '-1px',
                letterSpacing: '0.04em',
                transition: 'color 0.2s ease',
              }}
            >
              {m === 'signup' ? 'new here' : 'sign in'}
            </button>
          ))}
        </div>

        {/* Error message */}
        {error && (
          <div style={{
            fontSize: '13px',
            color: '#c0392b',
            fontFamily: 'sans-serif',
            marginBottom: '24px',
            padding: '12px',
            background: '#fdf0ef',
            borderRadius: '2px',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>

          {isSignup && (
            <div>
              <label style={labelStyle}>your name</label>
              <input
                type="text"
                placeholder="first name"
                value={name}
                onChange={e => setName(e.target.value)}
                required
                style={inputStyle}
              />
            </div>
          )}

          <div>
            <label style={labelStyle}>email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
                style={{ ...inputStyle, paddingRight: '32px' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(p => !p)}
                style={{
                  position: 'absolute', right: 0, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: '#bbb', fontSize: '12px', fontFamily: 'sans-serif', padding: '4px',
                }}
              >
                {showPassword ? 'hide' : 'show'}
              </button>
            </div>
          </div>

          {isSignup && (
            <>
              <div>
                <label style={labelStyle}>what are your current interests?</label>
                <textarea
                  placeholder="I follow NVIDIA and Jensen Huang closely, really into Formula 1..."
                  rows={4}
                  value={interests}
                  onChange={e => setInterests(e.target.value)}
                  required
                  style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.6' }}
                />
              </div>

              <div>
                <label style={labelStyle}>what do you want to understand better?</label>
                <textarea
                  placeholder="I want to understand geopolitics, how central banks work..."
                  rows={4}
                  value={learningGoals}
                  onChange={e => setLearningGoals(e.target.value)}
                  required
                  style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.6' }}
                />
              </div>
            </>
          )}

          {!isSignup && (
            <div style={{ textAlign: 'right', marginTop: '-12px' }}>
              <a href="/forgot-password" style={{ fontSize: '12px', color: '#bbb', textDecoration: 'none', letterSpacing: '0.04em' }}>
                forgot password?
              </a>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              background: loading ? '#999' : '#1a1a1a',
              color: '#f5f4f0',
              border: 'none',
              padding: '14px',
              fontSize: '13px',
              letterSpacing: '0.04em',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '8px',
              transition: 'background 0.2s ease',
            }}
          >
            {loading ? 'please wait...' : isSignup ? 'create my briefing' : 'sign in'}
          </button>

        </form>
      </div>
    </main>
  )
}