'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

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

function MobileArticleCard({ article, index }) {
  const [expanded, setExpanded] = useState(false)

  const tagLabel =
    index === 4 ? 'the world today' :
    index >= 3  ? 'something to learn' :
    'your stories'

  return (
    <div
      onClick={() => setExpanded(e => !e)}
      style={{
        borderBottom: '1px solid #e8e6e0',
        padding: '20px 0',
        cursor: 'pointer',
      }}
    >
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '12px',
      }}>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: '10px',
            fontFamily: 'sans-serif',
            color: '#bbb',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            marginBottom: '6px',
          }}>
            {tagLabel} · {article.source}
          </div>
          <div style={{
            fontSize: '15px',
            lineHeight: '1.4',
            color: '#1a1a1a',
            fontFamily: 'Georgia, serif',
          }}>
            {article.title}
          </div>
        </div>
        <div style={{
          fontSize: '16px',
          color: '#bbb',
          flexShrink: 0,
          marginTop: '2px',
          transition: 'transform 0.2s ease',
          transform: expanded ? 'rotate(45deg)' : 'rotate(0deg)',
        }}>
          +
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: '14px', animation: 'fadeIn 0.2s ease' }}>
          <p style={{
            fontSize: '13px',
            fontFamily: 'sans-serif',
            color: '#666',
            lineHeight: '1.7',
            marginBottom: '12px',
          }}>
            {article.summary || 'summary coming soon.'}
          </p>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
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
        padding: '80px 24px',
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
      padding: '64px 24px 80px',
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
        <div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '14px',
            flexWrap: 'wrap',
            gap: '6px',
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
            <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>
          </div>
        </div>

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

  // JS-driven wave animation for mobile (works on Safari/iOS unlike CSS d: path())
  useEffect(() => {
    if (!isMobile) return
    const p1 = document.getElementById('wave-path-1')
    const p2 = document.getElementById('wave-path-2')
    if (!p1 || !p2) return

    let raf
    function draw(ts) {
      const t = ts * 0.001
      const W = 800

      const y1 = (x) => 40 + Math.sin(x * 0.012 + t) * 18 + Math.sin(x * 0.007 - t * 1.3) * 10
      const y2 = (x) => 40 + Math.sin(x * 0.012 + t * 0.9) * 14 + Math.sin(x * 0.007 + t * 1.1) * 8

      const toPath = (fn) => {
        let d = ''
        for (let x = 0; x <= W; x += 4) {
          d += `${x === 0 ? 'M' : 'L'}${x},${fn(x).toFixed(1)} `
        }
        return d
      }
      
      //const pts = [0, 100, 200, 300, 400, 500, 600, 700, 800]
      //const toPath = (fn) =>
      //  pts.map((x, i) => `${i === 0 ? 'M' : 'L'}${x},${fn(x).toFixed(1)}`).join(' ')
      
      p1.setAttribute('d', toPath(y1))
      p2.setAttribute('d', toPath(y2))
      raf = requestAnimationFrame(draw)
    }

    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [isMobile])

  const greeting = userName
    ? `good morning, ${userName.split(' ')[0].toLowerCase()}.`
    : 'good morning.'

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric'
  }).toLowerCase()

  // ── MOBILE LAYOUT ──
  if (isMobile) {
    return (
      <>
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
            padding: '20px 24px',
            borderBottom: '1px solid #e8e6e0',
          }}>
            <span style={{ fontSize: '14px', letterSpacing: '0.06em' }}>resonance</span>
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
              <a href="/profile" style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em', textDecoration: 'none' }}>
                profile
              </a>
              <button
                onClick={() => { localStorage.removeItem('user_id'); localStorage.removeItem('user_name'); router.push('/') }}
                style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em' }}
              >
                sign out
              </button>
            </div>
          </nav>

          <div style={{ padding: '32px 24px 8px' }}>
            <div style={{ fontSize: '22px', fontWeight: '400', letterSpacing: '-0.01em', marginBottom: '6px' }}>
              {greeting}
            </div>
            <div style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em' }}>
              {today}
            </div>
          </div>

          {/* JS-animated wave — works on all mobile browsers */}
          <div style={{ position: 'relative', height: '80px', overflow: 'hidden', margin: '16px 0' }}>
            <svg
              style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
              viewBox="0 0 800 80"
              preserveAspectRatio="none"
            >
              <path id="wave-path-1" fill="none" stroke="#c8c4bc" strokeWidth="1.5" />
              <path id="wave-path-2" fill="none" stroke="#c8c4bc" strokeWidth="0.8" opacity="0.5" />
            </svg>
          </div>

          <div style={{ padding: '0 24px 8px' }}>
            <div style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              your briefing
            </div>
          </div>

          <div style={{ padding: '0 24px' }}>
            {loading && (
              <div style={{ padding: '40px 0', fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em' }}>
                preparing your briefing...
              </div>
            )}
            {error && (
              <div style={{ padding: '40px 0', fontSize: '13px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em', lineHeight: '1.7' }}>
                your briefing for today is being prepared.<br />check back soon.
              </div>
            )}
            {articles.map((article, i) => (
              <MobileArticleCard key={article.id} article={article} index={i} />
            ))}
          </div>

          {!loading && !error && articles.length > 0 && (
            <div style={{ padding: '24px 24px 0', textAlign: 'right' }}>
              <a href="#feedback" style={{ fontSize: '12px', fontFamily: 'sans-serif', color: '#999', letterSpacing: '0.06em', textDecoration: 'none' }}>
                share feedback ↓
              </a>
            </div>
          )}
        </main>

        <div id="feedback" style={{ backgroundColor: '#f5f4f0', paddingTop: '40px' }}>
          <FeedbackSection userId={userId} />
        </div>

        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to   { opacity: 1; transform: translateY(0); }
          }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          html { scroll-behavior: smooth; }
        `}</style>
      </>
    )
  }

  // ── DESKTOP LAYOUT ──
  return (
    <>
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
          <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
            <a href="/profile" style={{ fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', letterSpacing: '0.06em', textDecoration: 'none' }}>
              profile
            </a>
            <button
              onClick={() => { localStorage.removeItem('user_id'); localStorage.removeItem('user_name'); router.push('/') }}
              style={{ background: 'none', border: 'none', fontSize: '11px', fontFamily: 'sans-serif', color: '#bbb', cursor: 'pointer', letterSpacing: '0.06em' }}
            >
              sign out
            </button>
          </div>
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
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
      `}</style>
    </>
  )
}