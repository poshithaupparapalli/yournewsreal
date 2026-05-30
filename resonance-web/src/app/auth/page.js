'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const inputStyle = {
  width: '100%',
  border: 'none',
  borderBottom: '1px solid #d4d0c8',
  background: 'transparent',
  padding: '10px 0',
  fontSize: '14px',
  fontFamily: 'Georgia, serif',
  outline: 'none',
  color: '#1a1a1a',
}

const labelStyle = {
  fontSize: '11px',
  color: '#999',
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  display: 'block',
  marginBottom: '8px',
  fontFamily: 'sans-serif',
}


export default function AuthPage() {
  const router = useRouter()
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
          body: JSON.stringify({ name, email, password, interests, learning_goals: learningGoals }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Signup failed')
        localStorage.setItem('user_id', data.user_id)
        localStorage.setItem('user_name', name)
        // Kick off on-demand pipeline in background, then show waiting page
        fetch(`${API_URL}/run-pipeline/${data.user_id}`, { method: 'POST' })
        router.push('/waiting')
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
      fontFamily: 'Georgia, serif',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
    }}>
      <div style={{
        position: 'relative',
        zIndex: 1,
        maxWidth: '460px',
        width: '100%',
        padding: '48px 40px',
      }}>

        <a href="/" style={{
          fontSize: '12px',
          color: '#aaa',
          textDecoration: 'none',
          letterSpacing: '0.08em',
          display: 'block',
          marginBottom: '52px',
          fontFamily: 'sans-serif',
        }}>
          ← Resonance
        </a>

        <h1 style={{
          fontSize: '32px',
          fontWeight: '400',
          letterSpacing: '-0.01em',
          marginBottom: '8px',
          color: '#1a1a1a',
        }}>
          {isSignup ? 'Tell us about you.' : 'Welcome back.'}
        </h1>
        <p style={{
          fontSize: '14px',
          fontFamily: 'sans-serif',
          color: '#888',
          lineHeight: '1.6',
          marginBottom: '36px',
        }}>
          {isSignup
            ? 'Your answers shape every briefing you receive.'
            : 'Sign in to your Resonance account.'}
        </p>

        {/* Toggle */}
        <div style={{
          display: 'flex',
          marginBottom: '36px',
          borderBottom: '1px solid #e0ddd6',
        }}>
          {[['signup', 'New here'], ['login', 'Sign in']].map(([m, label]) => (
            <button
              key={m}
              onClick={() => { setMode(m); setError('') }}
              style={{
                background: 'none',
                border: 'none',
                padding: '10px 0',
                marginRight: '28px',
                fontSize: '13px',
                fontFamily: 'sans-serif',
                color: mode === m ? '#1a1a1a' : '#bbb',
                cursor: 'pointer',
                borderBottom: mode === m ? '1px solid #1a1a1a' : '1px solid transparent',
                marginBottom: '-1px',
                letterSpacing: '0.02em',
                transition: 'color 0.2s ease',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {error && (
          <div style={{
            fontSize: '13px',
            fontFamily: 'sans-serif',
            color: '#c0392b',
            marginBottom: '24px',
            padding: '12px 14px',
            background: '#fdf0ef',
            borderRadius: '2px',
            borderLeft: '2px solid #e74c3c',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>

          {isSignup && (
            <div>
              <label style={labelStyle}>Your name</label>
              <input
                type="text"
                placeholder="First name"
                value={name}
                onChange={e => setName(e.target.value)}
                required
                style={inputStyle}
              />
            </div>
          )}

          <div>
            <label style={labelStyle}>Email</label>
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
            <label style={labelStyle}>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                style={{ ...inputStyle, paddingRight: '40px' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(p => !p)}
                style={{
                  position: 'absolute', right: 0, top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: '#bbb', fontSize: '11px', fontFamily: 'sans-serif',
                  letterSpacing: '0.06em', padding: '4px',
                }}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          {!isSignup && (
            <div style={{ textAlign: 'right', marginTop: '-10px' }}>
              <a href="/forgot-password" style={{
                fontSize: '12px', fontFamily: 'sans-serif',
                color: '#bbb', textDecoration: 'none', letterSpacing: '0.04em',
              }}>
                Forgot password?
              </a>
            </div>
          )}

          {isSignup && (
            <>
              <div>
                <label style={labelStyle}>What are your current interests?</label>
                <textarea
                  placeholder="I follow NVIDIA and Jensen Huang closely, really into Formula 1..."
                  rows={4}
                  value={interests}
                  onChange={e => setInterests(e.target.value)}
                  required
                  style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.7' }}
                />
              </div>
              <div>
                <label style={labelStyle}>What do you want to understand better?</label>
                <textarea
                  placeholder="I want to understand geopolitics, how central banks work..."
                  rows={4}
                  value={learningGoals}
                  onChange={e => setLearningGoals(e.target.value)}
                  required
                  style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.7' }}
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              background: 'transparent',
              color: loading ? '#aaa' : '#1a1a1a',
              border: `1px solid ${loading ? '#ccc' : '#1a1a1a'}`,
              padding: '15px',
              fontSize: '13px',
              fontFamily: 'sans-serif',
              letterSpacing: '0.08em',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '8px',
              transition: 'all 0.2s ease',
            }}
          >
            {loading ? 'Please wait...' : isSignup ? 'Create my briefing' : 'Sign in'}
          </button>

        </form>
      </div>

      <style>{`
        @keyframes orbFloat {
          0%, 100% { transform: translateY(-50%) scale(1); }
          50% { transform: translateY(-52%) scale(1.03); }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input::placeholder, textarea::placeholder { color: #ccc; font-family: sans-serif; font-size: 13px; }
      `}</style>
    </main>
  )
}
