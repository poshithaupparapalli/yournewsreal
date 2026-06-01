'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false)
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])
  return isMobile
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const POSITIONS = [
  { left: '5%',  top: '18%' },
  { left: '38%', top: '14%' },
  { left: '71%', top: '18%' },
  { left: '18%', top: '62%' },
  { left: '55%', top: '62%' },
]

const SCORE_LABELS = {
  1: 'not relevant at all',
  2: 'mostly off',
  3: 'pretty good',
  4: 'very relevant',
  5: 'exactly right',
}

function BackgroundDots() {
  const dots = [
    { left: '8%',  top: '12%' }, { left: '92%', top: '8%'  },
    { left: '45%', top: '6%'  }, { left: '78%', top: '22%' },
    { left: '15%', top: '38%' }, { left: '88%', top: '45%' },
    { left: '3%',  top: '55%' }, { left: '60%', top: '75%' },
    { left: '30%', top: '82%' }, { left: '95%', top: '70%' },
    { left: '52%', top: '88%' }, { left: '20%', top: '65%' },
    { left: '70%', top: '52%' }, { left: '38%', top: '30%' },
  ]
  return (
    <>
      {dots.map((d, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: d.left, top: d.top,
          width: '2.5px', height: '2.5px',
          borderRadius: '50%',
          background: '#c4c0b8',
          opacity: 0.5,
          pointerEvents: 'none',
        }} />
      ))}
    </>
  )
}

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

function FloatingParticles() {
  const particles = [
    { left: '20%', delay: '0s',    duration: '3.2s' },
    { left: '35%', delay: '0.6s',  duration: '2.8s' },
    { left: '50%', delay: '1.1s',  duration: '3.5s' },
    { left: '65%', delay: '0.3s',  duration: '2.6s' },
    { left: '80%', delay: '0.9s',  duration: '3.1s' },
    { left: '28%', delay: '1.4s',  duration: '2.9s' },
    { left: '72%', delay: '0.5s',  duration: '3.4s' },
  ]
  return (
    <div style={{ position: 'relative', height: '100px', overflow: 'hidden', background: '#f5f4f0' }}>
      {particles.map((p, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            top: '-6px',
            left: p.left,
            width: '3px',
            height: '3px',
            borderRadius: '50%',
            background: '#c8c4bc',
            animation: `floatDown ${p.duration} ease-in-out infinite`,
            animationDelay: p.delay,
          }}
        />
      ))}
    </div>
  )
}

function MobileArticleCard({ article, isExpanded, onTap }) {
  return (
    <div
      onClick={() => onTap(isExpanded ? null : article.id)}
      style={{
        padding: '20px 0',
        borderBottom: '1px solid #e8e6e0',
        cursor: 'pointer',
        position: 'relative',
        zIndex: 5,
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
        fontSize: '17px',
        lineHeight: '1.4',
        color: '#1a1a1a',
        fontFamily: 'Georgia, serif',
      }}>
        {article.title}
      </div>
      {isExpanded && (
        <div style={{ animation: 'fadeIn 0.25s ease' }}>
          <div style={{
            fontSize: '14px',
            fontFamily: 'sans-serif',
            color: '#666',
            lineHeight: '1.65',
            marginTop: '12px',
            marginBottom: '16px',
          }}>
            {article.summary || 'summary coming soon.'}
          </div>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            style={{
              fontSize: '12px',
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

function ArticleCard({ article, onHover, isExpanded }) {
  return (
    <div
      onMouseEnter={() => onHover(article.id)}
      onMouseLeave={() => onHover(null)}
      style={{
        position: 'absolute',
        left: article.position.left,
        top: article.position.top,
        maxWidth: '300px',
        cursor: 'default',
        background: isExpanded ? 'rgba(245, 244, 240, 0.92)' : 'transparent',
        padding: isExpanded ? '16px' : '0',
        backdropFilter: isExpanded ? 'blur(4px)' : 'none',
        transition: 'padding 0.3s ease, background 0.3s ease',
        zIndex: isExpanded ? 20 : 1,
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

function FeedbackSection({ userId }) {
  const [score, setScore] = useState(3)
  const [text, setText] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, score, text }),
      })
    } catch (_) {}
    setSubmitted(true)
    setLoading(false)
  }

  if (submitted) {
    return (
      <section style={{
        maxWidth: '520px',
        margin: '0 auto',
        padding: '80px 48px',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '13px', fontFamily: 'sans-serif', color: '#999', letterSpacing: '0.06em' }}>
          thank you. this genuinely helps us get better.
        </div>
      </section>
    )
  }

  return (
    <section style={{
      maxWidth: '520px',
      margin: '0 auto',
      padding: '64px 48px 80px',
    }}>
      <div style={{
        fontSize: '11px',
        fontFamily: 'sans-serif',
        color: '#bbb',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        marginBottom: '16px',
      }}>
        Feedback
      </div>
      <h2 style={{
        fontFamily: 'Georgia, serif',
        fontSize: '26px',
        fontWeight: '400',
        color: '#1a1a1a',
        marginBottom: '10px',
        letterSpacing: '-0.01em',
      }}>
        How was today's briefing?
      </h2>
      <p style={{
        fontSize: '13px',
        fontFamily: 'sans-serif',
        color: '#999',
        lineHeight: '1.6',
        marginBottom: '40px',
      }}>
        We're just getting started. Brutal honesty is genuinely appreciated.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '36px' }}>

        {/* Relevance slider */}
        <div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '14px',
          }}>
            <label style={{ fontSize: '12px', fontFamily: 'sans-serif', color: '#666', letterSpacing: '0.04em' }}>
              How relevant were the articles?
            </label>
            <span style={{ fontSize: '12px', fontFamily: 'sans-serif', color: '#aaa', fontStyle: 'italic' }}>
              {SCORE_LABELS[score]}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="5"
            value={score}
            onChange={e => setScore(Number(e.target.value))}
            style={{ width: '100%', accentColor: '#1a1a1a', cursor: 'pointer' }}
          />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '6px',
            fontSize: '10px',
            fontFamily: 'sans-serif',
            color: '#ccc',
            letterSpacing: '0.04em',
          }}>
            <span>1</span>
            <span>2</span>
            <span>3</span>
            <span>4</span>
            <span>5</span>
          </div>
        </div>

        {/* Text feedback */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '12px',
            fontFamily: 'sans-serif',
            color: '#666',
            letterSpacing: '0.04em',
            marginBottom: '12px',
          }}>
            What would make this better?
          </label>
          <textarea
            placeholder="wrong topics, too long, missing something... anything helps."
            value={text}
            onChange={e => setText(e.target.value)}
            rows={4}
            style={{
              width: '100%',
              border: 'none',
              borderBottom: '1px solid #ddd',
              background: 'transparent',
              fontSize: '13px',
              fontFamily: 'sans-serif',
              color: '#1a1a1a',
              lineHeight: '1.7',
              resize: 'none',
              outline: 'none',
              padding: '0 0 8px',
            }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            background: 'transparent',
            color: loading ? '#aaa' : '#1a1a1a',
            border: `1px solid ${loading ? '#ccc' : '#1a1a1a'}`,
            padding: '13px',
            fontSize: '12px',
            fontFamily: 'sans-serif',
            letterSpacing: '0.06em',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          {loading ? 'Sending...' : 'Submit feedback'}
        </button>
      </form>
    </section>
  )
}

export default function BriefingPage() {
  const router = useRouter()
  const isMobile = useIsMobile()
  const [userName, setUserName] = useState('')
  const [userId, setUserId] = useState('')
  const [hoveredCard, setHoveredCard] = useState(null)
  const [selectedCard, setSelectedCard] = useState(null)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const name = localStorage.getItem('user_name')
    const uid  = localStorage.getItem('user_id')
    if (!uid) { router.push('/auth'); return }
    setUserName(name || '')
    setUserId(uid)

    fetch(`${API_URL}/briefing/${uid}`)
      .then(res => {
        if (!res.ok) throw new Error('no briefing yet')
        return res.json()
      })
      .then(data => {
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

  if (isMobile) return (
    <>
      <main style={{
        backgroundColor: '#f5f4f0',
        minHeight: '100vh',
        position: 'relative',
        fontFamily: 'Georgia, serif',
        color: '#1a1a1a',
        overflowX: 'hidden',
      }}>
        {/* Nav */}
        <nav style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          padding: '24px 24px 0',
          position: 'relative',
          zIndex: 10,
        }}>
          <span style={{ fontSize: '13px', letterSpacing: '0.06em' }}>resonance</span>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '13px', fontFamily: 'Georgia, serif', color: '#1a1a1a' }}>{greeting}</div>
            <div style={{ fontSize: '10px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em', marginTop: '2px' }}>{today}</div>
          </div>
          <button
            onClick={() => { localStorage.removeItem('user_id'); localStorage.removeItem('user_name'); router.push('/') }}
            style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em' }}
          >
            sign out
          </button>
        </nav>

        {/* Wave */}
        <div style={{ position: 'relative', height: '120px', overflow: 'hidden', marginTop: '16px' }}>
          <BackgroundDots />
          <svg
            style={{ position: 'absolute', top: '50%', left: 0, width: '100%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
            height="120"
            viewBox="0 0 390 120"
            preserveAspectRatio="none"
          >
            <path
              d="M0,60 C65,15 130,105 195,60 C260,15 325,105 390,60"
              fill="none" stroke="#c8c4bc" strokeWidth="1.5"
              style={{ animation: 'wave 4s ease-in-out infinite alternate' }}
            />
            <path
              d="M0,65 C55,20 120,110 195,65 C270,20 335,110 390,65"
              fill="none" stroke="#c8c4bc" strokeWidth="0.8" opacity="0.5"
              style={{ animation: 'wave 5s ease-in-out infinite alternate-reverse' }}
            />
          </svg>
        </div>

        {/* Articles */}
        <div style={{ padding: '0 24px 40px', position: 'relative', zIndex: 5 }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '40px 0', fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em' }}>
              preparing your briefing...
            </div>
          )}
          {error && (
            <div style={{ textAlign: 'center', padding: '40px 0', fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em', lineHeight: '1.7' }}>
              your briefing for today is being prepared.<br />check back soon.
            </div>
          )}
          {articles.map(article => (
            <MobileArticleCard
              key={article.id}
              article={article}
              isExpanded={selectedCard === article.id}
              onTap={setSelectedCard}
            />
          ))}
        </div>

        {/* Bottom bar */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #e8e6e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div style={{ fontSize: '10px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.08em' }}>
            your stories · learn · world
          </div>
          <a href="#feedback-mobile" style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#666', letterSpacing: '0.06em', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#999', animation: 'pulse 2s ease-in-out infinite', flexShrink: 0 }} />
            feedback ↓
          </a>
        </div>
      </main>

      <div id="feedback-mobile" style={{ backgroundColor: '#f5f4f0', paddingTop: '40px' }}>
        <FeedbackSection userId={userId} />
      </div>
    </>
  )

  return (
    <>
      {/* ── BRIEFING SECTION ── */}
      <main style={{
        backgroundColor: '#f5f4f0',
        height: '100vh',
        overflow: 'visible',
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
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '13px', fontFamily: 'Georgia, serif', color: '#1a1a1a', letterSpacing: '0.02em' }}>
              {greeting}
            </div>
            <div style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em', marginTop: '2px' }}>
              {today}
            </div>
          </div>
          <button
            onClick={() => { localStorage.removeItem('user_id'); localStorage.removeItem('user_name'); router.push('/') }}
            style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em' }}
          >
            sign out
          </button>
        </nav>

        <BackgroundDots />
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
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '20px 48px',
          borderTop: '1px solid #e8e6e0',
        }}>
          <div style={{ display: 'flex', gap: '32px', alignItems: 'center' }}>
            {['01 your stories', '02 something to learn', '03 the world today'].map((label, i, arr) => (
              <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
                <span style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.08em' }}>
                  {label}
                </span>
                {i < arr.length - 1 && <span style={{ color: '#ddd' }}>—</span>}
              </span>
            ))}
          </div>
          <a
            href="#feedback"
            style={{ fontSize: '12px', fontFamily: 'sans-serif', color: '#666', letterSpacing: '0.08em', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <span style={{
              display: 'inline-block',
              width: '7px', height: '7px',
              borderRadius: '50%',
              background: '#999',
              animation: 'pulse 2s ease-in-out infinite',
              flexShrink: 0,
            }} />
            share feedback ↓
          </a>
        </div>
      </main>

      {/* ── FEEDBACK SECTION ── */}
      <div id="feedback" style={{
        backgroundColor: '#f5f4f0',
        paddingTop: '60px',
        opacity: hoveredCard ? 0 : 1,
        pointerEvents: hoveredCard ? 'none' : 'auto',
        transition: 'opacity 0.3s ease',
      }}>
        <FeedbackSection userId={userId} />
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.4; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.4); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatDown {
          0%   { transform: translateY(0px);  opacity: 0; }
          20%  { opacity: 1; }
          80%  { opacity: 1; }
          100% { transform: translateY(100px); opacity: 0; }
        }
        @keyframes wave {
          from { d: path("M0,60 C65,15 130,105 195,60 C260,15 325,105 390,60"); }
          to   { d: path("M0,60 C65,105 130,15 195,60 C260,105 325,15 390,60"); }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
      `}</style>
    </>
  )
}
