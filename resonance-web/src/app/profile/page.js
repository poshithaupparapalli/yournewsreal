'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const labelStyle = {
  fontSize: '11px',
  color: '#999',
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  display: 'block',
  marginBottom: '8px',
  fontFamily: 'sans-serif',
}

const valueStyle = {
  fontSize: '14px',
  fontFamily: 'Georgia, serif',
  color: '#1a1a1a',
  lineHeight: '1.7',
  whiteSpace: 'pre-wrap',
}

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

const dividerStyle = {
  borderBottom: '1px solid #e8e6e0',
  paddingBottom: '32px',
  marginBottom: '32px',
}

export default function ProfilePage() {
  const router = useRouter()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Email editing state
  const [editingEmail, setEditingEmail] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [emailSaving, setEmailSaving] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [emailSuccess, setEmailSuccess] = useState(false)

  useEffect(() => {
    const userId = localStorage.getItem('user_id')
    if (!userId) { router.push('/auth'); return }

    fetch(`${API_URL}/users/${userId}`)
      .then(res => {
        if (!res.ok) throw new Error('Could not load profile')
        return res.json()
      })
      .then(data => {
        setProfile(data)
        setNewEmail(data.email)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  async function handleSaveEmail(e) {
    e.preventDefault()
    setEmailError('')
    setEmailSuccess(false)
    setEmailSaving(true)

    const userId = localStorage.getItem('user_id')
    try {
      const res = await fetch(`${API_URL}/users/${userId}/email`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newEmail }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to update email')
      setProfile(p => ({ ...p, email: data.email }))
      setEmailSuccess(true)
      setEditingEmail(false)
    } catch (err) {
      setEmailError(err.message)
    } finally {
      setEmailSaving(false)
    }
  }

  function handleSignOut() {
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_name')
    router.push('/')
  }

  return (
    <main style={{
      backgroundColor: '#f5f4f0',
      minHeight: '100vh',
      fontFamily: 'Georgia, serif',
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
        <a href="/briefing" style={{
          fontSize: '14px',
          letterSpacing: '0.06em',
          textDecoration: 'none',
          color: '#1a1a1a',
        }}>
          resonance
        </a>
        <button
          onClick={handleSignOut}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '11px',
            fontFamily: 'sans-serif',
            color: '#bbb',
            cursor: 'pointer',
            letterSpacing: '0.06em',
          }}
        >
          sign out
        </button>
      </nav>

      {/* Content */}
      <div style={{
        maxWidth: '560px',
        margin: '0 auto',
        padding: '56px 40px 80px',
      }}>

        <a href="/briefing" style={{
          fontSize: '12px',
          color: '#aaa',
          textDecoration: 'none',
          letterSpacing: '0.08em',
          display: 'block',
          marginBottom: '40px',
          fontFamily: 'sans-serif',
        }}>
          ← back to briefing
        </a>

        <h1 style={{
          fontSize: '32px',
          fontWeight: '400',
          letterSpacing: '-0.01em',
          marginBottom: '8px',
        }}>
          Your profile.
        </h1>
        <p style={{
          fontSize: '14px',
          fontFamily: 'sans-serif',
          color: '#888',
          lineHeight: '1.6',
          marginBottom: '48px',
        }}>
          This is what shapes your briefings.
        </p>

        {loading && (
          <div style={{ fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em' }}>
            loading...
          </div>
        )}

        {error && (
          <div style={{ fontSize: '13px', fontFamily: 'sans-serif', color: '#c0392b' }}>
            {error}
          </div>
        )}

        {profile && (
          <>
            {/* Name */}
            <div style={dividerStyle}>
              <label style={labelStyle}>Name</label>
              <div style={valueStyle}>{profile.name}</div>
            </div>

            {/* Email */}
            <div style={dividerStyle}>
              <label style={labelStyle}>Email</label>
              {!editingEmail ? (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '16px' }}>
                  <div style={valueStyle}>{profile.email}</div>
                  <button
                    onClick={() => { setEditingEmail(true); setEmailSuccess(false) }}
                    style={{
                      background: 'none',
                      border: 'none',
                      fontSize: '11px',
                      fontFamily: 'sans-serif',
                      color: '#bbb',
                      cursor: 'pointer',
                      letterSpacing: '0.06em',
                      flexShrink: 0,
                      padding: 0,
                    }}
                  >
                    edit
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSaveEmail}>
                  <input
                    type="email"
                    value={newEmail}
                    onChange={e => setNewEmail(e.target.value)}
                    required
                    autoFocus
                    style={inputStyle}
                  />
                  {emailError && (
                    <div style={{
                      fontSize: '12px',
                      fontFamily: 'sans-serif',
                      color: '#c0392b',
                      marginTop: '8px',
                    }}>
                      {emailError}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
                    <button
                      type="submit"
                      disabled={emailSaving}
                      style={{
                        background: 'transparent',
                        color: emailSaving ? '#aaa' : '#1a1a1a',
                        border: `1px solid ${emailSaving ? '#ccc' : '#1a1a1a'}`,
                        padding: '10px 20px',
                        fontSize: '12px',
                        fontFamily: 'sans-serif',
                        letterSpacing: '0.06em',
                        cursor: emailSaving ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {emailSaving ? 'Saving...' : 'Save'}
                    </button>
                    <button
                      type="button"
                      onClick={() => { setEditingEmail(false); setNewEmail(profile.email); setEmailError('') }}
                      style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '12px',
                        fontFamily: 'sans-serif',
                        color: '#bbb',
                        cursor: 'pointer',
                        letterSpacing: '0.06em',
                        padding: 0,
                      }}
                    >
                      cancel
                    </button>
                  </div>
                </form>
              )}
              {emailSuccess && (
                <div style={{
                  fontSize: '12px',
                  fontFamily: 'sans-serif',
                  color: '#999',
                  marginTop: '8px',
                  letterSpacing: '0.04em',
                }}>
                  email updated.
                </div>
              )}
            </div>

            {/* Interests */}
            <div style={dividerStyle}>
              <label style={labelStyle}>What you told us you follow</label>
              <div style={valueStyle}>
                {profile.interests_raw || <span style={{ color: '#ccc' }}>nothing recorded</span>}
              </div>
            </div>

            {/* Learning Goals */}
            <div style={{ paddingBottom: '32px' }}>
              <label style={labelStyle}>What you want to understand better</label>
              <div style={valueStyle}>
                {profile.learning_goals_raw || <span style={{ color: '#ccc' }}>nothing recorded</span>}
              </div>
            </div>
          </>
        )}
      </div>

      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input::placeholder { color: #ccc; font-family: sans-serif; font-size: 13px; }
        @media (max-width: 600px) {
          nav { padding: 20px 24px !important; }
          div[style*="max-width: 560px"] { padding: 40px 24px 60px !important; }
        }
      `}</style>
    </main>
  )
}