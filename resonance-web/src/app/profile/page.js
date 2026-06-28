'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.resonance-news.com'

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
  resize: 'vertical',
  lineHeight: '1.7',
}

const dividerStyle = {
  borderBottom: '1px solid #e8e6e0',
  paddingBottom: '32px',
  marginBottom: '32px',
}

// ── Share Modal ──────────────────────────────────────────────────────────────

function ShareModal({ userId, onUnlocked, onClose }) {
  const [copied, setCopied] = useState(false)
  const shareUrl = `${SITE_URL}/auth?ref=${userId}`

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(shareUrl)
    } catch {
      // Fallback for older browsers
      const el = document.createElement('textarea')
      el.value = shareUrl
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
    }

    setCopied(true)

    // Mark as shared on the backend
    await fetch(`${API_URL}/users/${userId}/share`, { method: 'POST' })

    // Short delay so user sees the "copied!" state, then unlock
    setTimeout(() => {
      onUnlocked()
      onClose()
    }, 1000)
  }

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(245, 244, 240, 0.85)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
    }}>
      <div style={{
        background: '#f5f4f0',
        border: '1px solid #e0ddd6',
        maxWidth: '420px',
        width: '90%',
        padding: '40px',
      }}>
        <div style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '16px' }}>
          Share to unlock
        </div>
        <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '24px', fontWeight: '400', color: '#1a1a1a', marginBottom: '12px', letterSpacing: '-0.01em' }}>
          Share Resonance with a friend.
        </h2>
        <p style={{ fontSize: '13px', fontFamily: 'sans-serif', color: '#888', lineHeight: '1.7', marginBottom: '32px' }}>
          Copy your link and send it to someone. Once you copy it, editing unlocks permanently.
        </p>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          border: '1px solid #e0ddd6',
          padding: '12px 14px',
          marginBottom: '20px',
          gap: '12px',
        }}>
          <span style={{
            fontSize: '12px',
            fontFamily: 'sans-serif',
            color: '#999',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            letterSpacing: '0.02em',
          }}>
            {shareUrl}
          </span>
          <button
            onClick={handleCopy}
            style={{
              background: copied ? 'transparent' : '#1a1a1a',
              color: copied ? '#999' : '#f5f4f0',
              border: copied ? '1px solid #ddd' : '1px solid #1a1a1a',
              padding: '8px 16px',
              fontSize: '11px',
              fontFamily: 'sans-serif',
              letterSpacing: '0.06em',
              cursor: 'pointer',
              flexShrink: 0,
              transition: 'all 0.2s ease',
            }}
          >
            {copied ? 'copied!' : 'Copy link'}
          </button>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '11px',
            fontFamily: 'sans-serif',
            color: '#ccc',
            cursor: 'pointer',
            letterSpacing: '0.06em',
            padding: 0,
          }}
        >
          cancel
        </button>
      </div>
    </div>
  )
}

// ── Editable field (interests or learning goals) ─────────────────────────────

function EditableField({ label, value, fieldKey, userId, hasShared, onSaved }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [showShareModal, setShowShareModal] = useState(false)
  const [unlocked, setUnlocked] = useState(hasShared)

  function handleEditClick() {
    if (!unlocked) {
      setShowShareModal(true)
    } else {
      setEditing(true)
    }
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaveError('')
    setSaving(true)
    try {
      const res = await fetch(`${API_URL}/users/${userId}/profile`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [fieldKey]: draft }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to save')
      onSaved(fieldKey, draft)
      setEditing(false)
    } catch (err) {
      setSaveError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      {showShareModal && (
        <ShareModal
          userId={userId}
          onUnlocked={() => setUnlocked(true)}
          onClose={() => setShowShareModal(false)}
        />
      )}

      <div>
        <label style={labelStyle}>{label}</label>

        {!editing ? (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
            <div style={valueStyle}>
              {value || <span style={{ color: '#ccc' }}>nothing recorded</span>}
            </div>
            <button
              onClick={handleEditClick}
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
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              {!unlocked && (
                <span style={{ fontSize: '10px' }}>🔒</span>
              )}
              edit
            </button>
          </div>
        ) : (
          <form onSubmit={handleSave}>
            <textarea
              value={draft}
              onChange={e => setDraft(e.target.value)}
              rows={4}
              autoFocus
              style={inputStyle}
            />
            {saveError && (
              <div style={{ fontSize: '12px', fontFamily: 'sans-serif', color: '#c0392b', marginTop: '8px' }}>
                {saveError}
              </div>
            )}
            <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
              <button
                type="submit"
                disabled={saving}
                style={{
                  background: 'transparent',
                  color: saving ? '#aaa' : '#1a1a1a',
                  border: `1px solid ${saving ? '#ccc' : '#1a1a1a'}`,
                  padding: '10px 20px',
                  fontSize: '12px',
                  fontFamily: 'sans-serif',
                  letterSpacing: '0.06em',
                  cursor: saving ? 'not-allowed' : 'pointer',
                }}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                type="button"
                onClick={() => { setEditing(false); setDraft(value); setSaveError('') }}
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
      </div>
    </>
  )
}

// ── Main Profile Page ────────────────────────────────────────────────────────

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

  function handleFieldSaved(fieldKey, newValue) {
    setProfile(p => ({ ...p, [fieldKey]: newValue }))
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
      <nav style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '24px 48px',
        borderBottom: '1px solid #e8e6e0',
      }}>
        <a href="/briefing" style={{ fontSize: '14px', letterSpacing: '0.06em', textDecoration: 'none', color: '#1a1a1a' }}>
          resonance
        </a>
        <button
          onClick={handleSignOut}
          style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em' }}
        >
          sign out
        </button>
      </nav>

      <div style={{ maxWidth: '560px', margin: '0 auto', padding: '56px 40px 80px' }}>

        <a href="/briefing" style={{ fontSize: '12px', color: '#aaa', textDecoration: 'none', letterSpacing: '0.08em', display: 'block', marginBottom: '40px', fontFamily: 'sans-serif' }}>
          ← back to briefing
        </a>

        <h1 style={{ fontSize: '32px', fontWeight: '400', letterSpacing: '-0.01em', marginBottom: '8px' }}>
          Your profile.
        </h1>
        <p style={{ fontSize: '14px', fontFamily: 'sans-serif', color: '#888', lineHeight: '1.6', marginBottom: '48px' }}>
          This is what shapes your briefings.
        </p>

        {loading && (
          <div style={{ fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em' }}>loading...</div>
        )}
        {error && (
          <div style={{ fontSize: '13px', fontFamily: 'sans-serif', color: '#c0392b' }}>{error}</div>
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
                    style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em', flexShrink: 0, padding: 0 }}
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
                    style={{ ...inputStyle, resize: 'none' }}
                  />
                  {emailError && (
                    <div style={{ fontSize: '12px', fontFamily: 'sans-serif', color: '#c0392b', marginTop: '8px' }}>{emailError}</div>
                  )}
                  <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
                    <button type="submit" disabled={emailSaving} style={{ background: 'transparent', color: emailSaving ? '#aaa' : '#1a1a1a', border: `1px solid ${emailSaving ? '#ccc' : '#1a1a1a'}`, padding: '10px 20px', fontSize: '12px', fontFamily: 'sans-serif', letterSpacing: '0.06em', cursor: emailSaving ? 'not-allowed' : 'pointer' }}>
                      {emailSaving ? 'Saving...' : 'Save'}
                    </button>
                    <button type="button" onClick={() => { setEditingEmail(false); setNewEmail(profile.email); setEmailError('') }} style={{ background: 'none', border: 'none', fontSize: '12px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em', padding: 0 }}>
                      cancel
                    </button>
                  </div>
                </form>
              )}
              {emailSuccess && (
                <div style={{ fontSize: '12px', fontFamily: 'sans-serif', color: '#999', marginTop: '8px', letterSpacing: '0.04em' }}>email updated.</div>
              )}
            </div>

            {/* Interests */}
            <div style={dividerStyle}>
              <EditableField
                label="What you told us you follow"
                value={profile.interests_raw}
                fieldKey="interests_raw"
                userId={profile.id}
                hasShared={profile.has_shared}
                onSaved={handleFieldSaved}
              />
            </div>

            {/* Learning Goals */}
            <div>
              <EditableField
                label="What you want to understand better"
                value={profile.learning_goals_raw}
                fieldKey="learning_goals_raw"
                userId={profile.id}
                hasShared={profile.has_shared}
                onSaved={handleFieldSaved}
              />
            </div>
          </>
        )}
      </div>

      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input::placeholder, textarea::placeholder { color: #ccc; font-family: sans-serif; font-size: 13px; }
        @media (max-width: 600px) {
          nav { padding: 20px 24px !important; }
        }
      `}</style>
    </main>
  )
}