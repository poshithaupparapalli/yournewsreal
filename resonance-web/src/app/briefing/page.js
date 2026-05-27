'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

// Fixed positions — 3 above the wave, 2 below
const POSITIONS = [
  { left: '5%',  top: '18%' },
  { left: '38%', top: '14%' },
  { left: '71%', top: '18%' },
  { left: '18%', top: '62%' },
  { left: '55%', top: '62%' },
]

function Wave() {
  return (
    <svg
      style={{
        position: 'absolute',
        top: '50%',
        left: 0,
        width: '100%',
        transform: 'translateY(-50%)',
        pointerEvents: 'none',
      }}
      height="200"
      viewBox="0 0 1440 200"
      preserveAspectRatio="none"
    >
      <path
        d="M0,100 C240,20 480,180 720,100 C960,20 1200,180 1440,100"
        fill="none"
        stroke="#c8c4bc"
        strokeWidth="1.5"
        style={{ animation: 'wave 4s ease-in-out infinite alternate' }}
      />
      <path
        d="M0,110 C200,30 440,190 720,110 C1000,30 1240,190 1440,110"
        fill="none"
        stroke="#c8c4bc"
        strokeWidth="0.8"
        opacity="0.5"
        style={{ animation: 'wave 5s ease-in-out infinite alternate-reverse' }}
      />
      <style>{`
        @keyframes wave {
          from { d: path("M0,100 C240,20 480,180 720,100 C960,20 1200,180 1440,100"); }
          to   { d: path("M0,100 C240,180 480,20 720,100 C960,180 1200,20 1440,100"); }
        }
      `}</style>
    </svg>
  )
}

function ArticleCard({ article, onHover, isExpanded }) {
  return (
    <div
      onMouseEnter={() => onHover(article.id)}
      onMouseLeave={() => onHover(null)}
      style={{
        position: 'absolute',
        left: article.position.left,
        top: article.position.top,
        maxWidth: '260px',
        cursor: 'default',
      }}
    >
      <div style={{
        fontSize: '10px',
        fontFamily: 'sans-serif',
        color: '#aaa',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        marginBottom: '6px',
      }}>
        {article.source}
      </div>

      <div style={{
        fontSize: '15px',
        lineHeight: '1.35',
        color: '#1a1a1a',
        marginBottom: isExpanded ? '12px' : '0',
        transition: 'margin 0.3s ease',
      }}>
        {article.title}
      </div>

      {isExpanded && (
        <div style={{ animation: 'fadeIn 0.25s ease' }}>
          <div style={{
            fontSize: '13px',
            fontFamily: 'sans-serif',
            color: '#666',
            lineHeight: '1.65',
            marginBottom: '12px',
          }}>
            {article.summary || 'summary coming soon.'}
          </div>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '11px',
              fontFamily: 'sans-serif',
              color: '#999',
              letterSpacing: '0.06em',
              textDecoration: 'none',
              borderBottom: '1px solid #ddd',
              paddingBottom: '2px',
            }}
          >
            read full article →
          </a>
        </div>
      )}
    </div>
  )
}

export default function BriefingPage() {
  const router = useRouter()
  const [userName, setUserName] = useState('')
  const [hoveredCard, setHoveredCard] = useState(null)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const name   = localStorage.getItem('user_name')
    const userId = localStorage.getItem('user_id')
    if (!userId) { router.push('/auth'); return }
    setUserName(name || '')

    // Fetch today's briefing from FastAPI
    fetch(`http://localhost:8000/briefing/${userId}`)
      .then(res => {
        if (!res.ok) throw new Error('no briefing yet')
        return res.json()
      })
      .then(data => {
        // Combine all articles and attach positions
        const all = [
          ...data.interests,
          ...data.learning,
          ...data.world,
        ].slice(0, 5).map((article, i) => ({
          ...article,
          position: POSITIONS[i],
        }))
        setArticles(all)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const greeting = userName
    ? `good morning, ${userName.split(' ')[0].toLowerCase()}.`
    : 'good morning.'

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric'
  }).toLowerCase()

  return (
    <main style={{
      backgroundColor: '#f5f4f0',
      height: '100vh',
      overflow: 'hidden',
      position: 'relative',
      fontFamily: 'Georgia, serif',
      color: '#1a1a1a',
    }}>

      <nav style={{
        position: 'absolute',
        top: 0, left: 0, right: 0,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '24px 48px',
        zIndex: 10,
      }}>
        <span style={{ fontSize: '14px', letterSpacing: '0.06em' }}>resonance</span>
        <div style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em' }}>
          {today} · {greeting}
        </div>
        <button
          onClick={() => { localStorage.removeItem('user_id'); localStorage.removeItem('user_name'); router.push('/') }}
          style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em' }}
        >
          sign out
        </button>
      </nav>

      <Wave />

      {loading && (
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em',
        }}>
          preparing your briefing...
        </div>
      )}

      {error && (
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em',
          textAlign: 'center',
        }}>
          your briefing for today is being prepared.<br />check back soon.
        </div>
      )}

      {articles.map(article => (
        <ArticleCard
          key={article.id}
          article={article}
          onHover={setHoveredCard}
          isExpanded={hoveredCard === article.id}
        />
      ))}

      <div style={{
        position: 'absolute',
        bottom: 0, left: 0, right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '32px',
        padding: '20px 48px',
        borderTop: '1px solid #e8e6e0',
      }}>
        {['01 your stories', '02 something to learn', '03 the world today'].map((label, i, arr) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.08em' }}>
              {label}
            </span>
            {i < arr.length - 1 && <span style={{ color: '#ddd' }}>—</span>}
          </span>
        ))}
      </div>

      {/* TODO: feedback — "how was today's briefing?" placeholder */}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
      `}</style>

    </main>
  )
}
