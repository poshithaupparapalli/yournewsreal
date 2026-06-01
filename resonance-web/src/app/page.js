'use client'

import { useEffect, useRef, useState } from 'react'

function useInView(threshold = 0.2) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) setInView(true)
    }, { threshold })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])
  return [ref, inView]
}

function FadeIn({ children, delay = 0, style = {} }) {
  const [ref, inView] = useInView()
  return (
    <div ref={ref} style={{
      opacity: inView ? 1 : 0,
      transform: inView ? 'translateY(0)' : 'translateY(24px)',
      transition: `opacity 0.8s ease ${delay}s, transform 0.8s ease ${delay}s`,
      ...style
    }}>
      {children}
    </div>
  )
}

function ParticleHero() {
  const containerRef = useRef(null)
  const canvasRef = useRef(null)
  const mouseRef = useRef({ x: -9999, y: -9999 })
  const particlesRef = useRef([])

  useEffect(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container) return
    const ctx = canvas.getContext('2d')

    const COLORS = ['#5daabc','#3d8fa3','#1d6e80','#8bcdd8','#2a7a8c','#a0d4dc','#1a5566']
    const N = 220

    function waveY(x, t, H) {
      return H * 0.5
        + Math.sin(x * 0.012 + t) * 48
        + Math.sin(x * 0.007 - t * 1.3) * 28
        + Math.sin(x * 0.02 + t * 0.7) * 14
    }

    function init() {
      const W = container.offsetWidth
      const H = container.offsetHeight
      canvas.width = W * devicePixelRatio
      canvas.height = H * devicePixelRatio
      canvas.style.width = W + 'px'
      canvas.style.height = H + 'px'
      ctx.scale(devicePixelRatio, devicePixelRatio)

      const t = performance.now() * 0.001
      particlesRef.current = Array.from({ length: N }, () => {
        const x = Math.random() * W
        const spread = (Math.random() - 0.5) * 140
        const hy = waveY(x, t, H) + spread
        return {
          x, y: hy, hx: x, hy,
          vx: 0, vy: 0,
          r: Math.random() * 5 + 1.5,
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          alpha: Math.random() * 0.5 + 0.3,
          spread,
          speed: Math.random() * 0.4 + 0.15,
          phase: Math.random() * Math.PI * 2,
        }
      })
    }

    let rafId
    function loop(ts) {
      const t = ts * 0.001
      const W = container.offsetWidth
      const H = container.offsetHeight
      const mouse = mouseRef.current

      ctx.clearRect(0, 0, W, H)

      for (const p of particlesRef.current) {
        p.hy = waveY(p.hx, t * p.speed + p.phase, H) + p.spread

        const dx = mouse.x - p.x
        const dy = mouse.y - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 90 && dist > 0) {
          const force = (90 - dist) / 90
          p.vx -= (dx / dist) * force * 3.5
          p.vy -= (dy / dist) * force * 3.5
        }

        p.vx += (p.hx - p.x) * 0.04
        p.vy += (p.hy - p.y) * 0.04
        p.vx *= 0.82
        p.vy *= 0.82
        p.x += p.vx
        p.y += p.vy

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.globalAlpha = p.alpha
        ctx.fill()
      }
      ctx.globalAlpha = 1
      rafId = requestAnimationFrame(loop)
    }

    const onMouseMove = (e) => {
      const rect = container.getBoundingClientRect()
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    }
    const onMouseLeave = () => {
      mouseRef.current = { x: -9999, y: -9999 }
    }

    const ro = new ResizeObserver(init)
    ro.observe(container)
    container.addEventListener('mousemove', onMouseMove)
    container.addEventListener('mouseleave', onMouseLeave)

    init()
    rafId = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(rafId)
      ro.disconnect()
      container.removeEventListener('mousemove', onMouseMove)
      container.removeEventListener('mouseleave', onMouseLeave)
    }
  }, [])

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height: '100vh',
        background: '#ffffff',
        overflow: 'hidden',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0, left: 0,
          width: '100%',
          height: '100%',
        }}
      />

      {/* Centered text */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center',
        zIndex: 2,
        pointerEvents: 'none',
      }}>
        <div style={{
          fontSize: 'clamp(64px, 10vw, 100px)',
          fontWeight: '400',
          letterSpacing: '-0.03em',
          color: '#1a1a1a',
          lineHeight: 1,
          marginBottom: '18px',
          fontFamily: "'Georgia', 'Times New Roman', serif",
        }}>
          resonance
        </div>
        <div style={{
          fontSize: 'clamp(14px, 2vw, 17px)',
          color: '#888',
          letterSpacing: '0.04em',
          fontStyle: 'italic',
          fontFamily: "'Georgia', 'Times New Roman', serif",
        }}>
          Stay effortlessly informed in an increasingly noisy world
        </div>
      </div>

      {/* Bottom-right CTA */}
      <a
        href="/auth"
        style={{
          position: 'absolute',
          bottom: '36px',
          right: '48px',
          zIndex: 2,
          fontFamily: 'sans-serif',
          fontSize: '13px',
          letterSpacing: '0.06em',
          color: '#1a1a1a',
          border: '1px solid #1a1a1a',
          padding: '10px 24px',
          textDecoration: 'none',
          background: 'transparent',
          transition: 'background 0.2s, color 0.2s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.background = '#1a1a1a'
          e.currentTarget.style.color = '#fff'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = 'transparent'
          e.currentTarget.style.color = '#1a1a1a'
        }}
      >
        get started →
      </a>

      {/* Scroll hint */}
      <div style={{
        position: 'absolute',
        bottom: '36px',
        left: '50%',
        transform: 'translateX(-50%)',
        fontSize: '12px',
        fontFamily: 'sans-serif',
        color: '#bbb',
        letterSpacing: '0.06em',
        zIndex: 2,
      }}>
        scroll to see how it works ↓
      </div>
    </div>
  )
}

export default function Home() {
  const [typed, setTyped] = useState('')
  const fullText = 'i follow NVIDIA and Jensen Huang closely. really into formula 1 racing and the business side of motorsport. also keeping up with what\'s happening at OpenAI and Anthropic.'

  useEffect(() => {
    let i = 0
    const interval = setInterval(() => {
      setTyped(fullText.slice(0, i))
      i++
      if (i > fullText.length) clearInterval(interval)
    }, 28)
    return () => clearInterval(interval)
  }, [])

  const s = {
    page: {
      backgroundColor: '#ffffff',
      fontFamily: "'Georgia', 'Times New Roman', serif",
      color: '#1a1a1a',
      overflowX: 'hidden',
    },
    nav: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '28px 48px',
      position: 'fixed',
      top: 0, left: 0, right: 0,
      zIndex: 100,
      backgroundColor: 'rgba(255,255,255,0.85)',
      backdropFilter: 'blur(8px)',
      borderBottom: '1px solid #e8e6e0',
    },
    navBrand: {
      fontSize: '15px',
      letterSpacing: '0.08em',
      fontFamily: 'sans-serif',
    },
    navLinks: {
      display: 'flex',
      gap: '32px',
      fontSize: '13px',
      fontFamily: 'sans-serif',
      color: '#666',
    },
    a: { textDecoration: 'none', color: 'inherit' },
    section: {
      maxWidth: '680px',
      margin: '0 auto',
      padding: '120px 48px',
    },
    divider: {
      maxWidth: '680px',
      margin: '0 auto',
      borderTop: '1px solid #e8e6e0',
    },
    label: {
      fontSize: '11px',
      fontFamily: 'sans-serif',
      color: '#999',
      letterSpacing: '0.1em',
      marginBottom: '48px',
    },
    body: {
      fontSize: '16px',
      fontFamily: 'sans-serif',
      lineHeight: '1.75',
      color: '#555',
      maxWidth: '480px',
      marginBottom: '48px',
    },
    card: {
      background: '#fff',
      border: '1px solid #e8e6e0',
      borderRadius: '4px',
      padding: '32px',
    },
  }

  return (
    <main style={s.page}>

      {/* Nav */}
      <nav style={s.nav}>
        <span style={s.navBrand}>resonance</span>
        <div style={s.navLinks}>
          <a href="#how" style={s.a}>how it works</a>
          <a href="#about" style={s.a}>about</a>
          <a href="/auth" style={s.a}>sign in</a>
        </div>
      </nav>

      {/* Hero — full viewport particle wave */}
      <ParticleHero />

      {/* HOW IT WORKS */}
      <div style={s.divider} id="how" />

      {/* Step 01 */}
      <section style={s.section}>
        <FadeIn>
          <div style={s.label}>01. Tell us about you</div>
        </FadeIn>
        <FadeIn delay={0.1}>
          <h2 style={{
            fontSize: 'clamp(28px, 4vw, 42px)',
            fontWeight: '400',
            letterSpacing: '-0.01em',
            lineHeight: '1.2',
            marginBottom: '24px',
          }}>
            Describe your interests<br />in your own words.
          </h2>
        </FadeIn>
        <FadeIn delay={0.2}>
          <p style={{ ...s.body, marginBottom: '40px' }}>
            No topic toggles. No checkbox lists. Just tell us what you follow,
            what you're curious about, and what you want to understand better.
          </p>
        </FadeIn>

        <FadeIn delay={0.3}>
          <div style={s.card}>
            <div style={{
              fontSize: '12px',
              fontFamily: 'sans-serif',
              color: '#999',
              letterSpacing: '0.06em',
              marginBottom: '20px',
            }}>
              What are your current interests?
            </div>
            <div style={{
              fontSize: '14px',
              fontFamily: 'sans-serif',
              color: '#333',
              lineHeight: '1.7',
              minHeight: '80px',
              borderBottom: '1px solid #e8e6e0',
              paddingBottom: '16px',
              marginBottom: '28px',
            }}>
              {typed}
              <span style={{
                borderRight: '1px solid #333',
                marginLeft: '1px',
                animation: 'blink 1s infinite',
              }} />
            </div>
            <div style={{
              fontSize: '12px',
              fontFamily: 'sans-serif',
              color: '#999',
              letterSpacing: '0.06em',
              marginBottom: '12px',
            }}>
              What do you want to understand better?
            </div>
            <div style={{
              fontSize: '14px',
              fontFamily: 'sans-serif',
              color: '#bbb',
              fontStyle: 'italic',
            }}>
              Geopolitics, how central banks work...
            </div>
          </div>
        </FadeIn>
      </section>

      <div style={s.divider} />

      {/* Step 02 */}
      <section style={s.section}>
        <FadeIn>
          <div style={s.label}>02. How we find your articles</div>
        </FadeIn>
        <FadeIn delay={0.1}>
          <h2 style={{
            fontSize: 'clamp(28px, 4vw, 42px)',
            fontWeight: '400',
            letterSpacing: '-0.01em',
            lineHeight: '1.2',
            marginBottom: '24px',
          }}>
            Not filtered by topic.<br />Matched by meaning.
          </h2>
        </FadeIn>
        <FadeIn delay={0.2}>
          <p style={{ ...s.body, marginBottom: '40px' }}>
            We read every article published that morning across dozens of sources.
            Our algorithm finds the ones whose meaning most closely aligns with yours,
            not just by keyword, but by semantic understanding.
          </p>
        </FadeIn>

        <FadeIn delay={0.3}>
          <div style={s.card}>
            <div style={{
              fontSize: '12px',
              fontFamily: 'sans-serif',
              color: '#999',
              letterSpacing: '0.06em',
              marginBottom: '20px',
            }}>
              Sources scanned this morning
            </div>
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
              marginBottom: '28px',
            }}>
              {['guardian', 'techcrunch', 'bbc', 'axios', 'the verge', 'ars technica', 'npr', 'al jazeera', 'eater', 'espn'].map(src => (
                <span key={src} style={{
                  fontSize: '11px',
                  fontFamily: 'sans-serif',
                  color: '#666',
                  background: '#f5f4f0',
                  border: '1px solid #e8e6e0',
                  padding: '4px 10px',
                  borderRadius: '2px',
                  letterSpacing: '0.04em',
                }}>
                  {src}
                </span>
              ))}
            </div>
            <div style={{
              borderTop: '1px solid #e8e6e0',
              paddingTop: '20px',
              fontSize: '12px',
              fontFamily: 'sans-serif',
              color: '#999',
            }}>
              1,400+ articles scanned → 9 selected for you
            </div>
          </div>
        </FadeIn>
      </section>

      <div style={s.divider} />

      {/* Step 03 */}
      <section style={s.section}>
        <FadeIn>
          <div style={s.label}>03. Your briefing</div>
        </FadeIn>
        <FadeIn delay={0.1}>
          <h2 style={{
            fontSize: 'clamp(28px, 4vw, 42px)',
            fontWeight: '400',
            letterSpacing: '-0.01em',
            lineHeight: '1.2',
            marginBottom: '24px',
          }}>
            Arrives every morning.<br />Nothing more.
          </h2>
        </FadeIn>
        <FadeIn delay={0.2}>
          <p style={{ ...s.body, marginBottom: '40px' }}>
            Five articles. A short summary of each. A link if you want to go deeper.
          </p>
        </FadeIn>

        <FadeIn delay={0.3}>
          <div style={s.card}>
            <div style={{
              fontSize: '11px',
              fontFamily: 'sans-serif',
              color: '#999',
              letterSpacing: '0.06em',
              marginBottom: '24px',
              paddingBottom: '16px',
              borderBottom: '1px solid #e8e6e0',
            }}>
              Your resonance, Friday, May 22
            </div>

            {[
              {
                tag: 'your interests',
                title: 'NVIDIA reports record quarterly earnings on AI chip demand',
                source: 'techcrunch',
                summary: 'NVIDIA posted $26B in quarterly revenue driven by data center GPU sales, as demand from hyperscalers continues to accelerate heading into 2026.',
              },
              {
                tag: 'your interests',
                title: 'Formula 1 considers radical sprint race format overhaul for 2027',
                source: 'the verge',
                summary: 'FIA officials confirmed discussions around expanding the sprint weekend format to six races, amid mixed reactions from team principals and fans.',
              },
              {
                tag: 'learning',
                title: 'How the Federal Reserve actually decides interest rates',
                source: 'axios',
                summary: 'A deep dive into the FOMC meeting process: who votes, what data they consider, and why small language changes in the statement move markets.',
              },
            ].map((article, i) => (
              <div key={i} style={{
                paddingBottom: '20px',
                marginBottom: '20px',
                borderBottom: i < 2 ? '1px solid #f0ede8' : 'none',
              }}>
                <div style={{
                  fontSize: '10px',
                  fontFamily: 'sans-serif',
                  color: '#bbb',
                  letterSpacing: '0.08em',
                  marginBottom: '6px',
                  textTransform: 'uppercase',
                }}>
                  {article.tag} · {article.source}
                </div>
                <div style={{
                  fontSize: '14px',
                  fontWeight: '500',
                  fontFamily: 'sans-serif',
                  color: '#1a1a1a',
                  marginBottom: '8px',
                  lineHeight: '1.4',
                }}>
                  {article.title}
                </div>
                <div style={{
                  fontSize: '13px',
                  fontFamily: 'sans-serif',
                  color: '#666',
                  lineHeight: '1.6',
                }}>
                  {article.summary}
                </div>
              </div>
            ))}

            <div style={{
              fontSize: '12px',
              fontFamily: 'sans-serif',
              color: '#bbb',
              marginTop: '8px',
            }}>
              + 2 more articles
            </div>
          </div>
        </FadeIn>
      </section>

      {/* About */}
      <div style={s.divider} id="about" />
      <section style={s.section}>
        <FadeIn>
          <div style={s.label}>About</div>
          <p style={{ ...s.body, marginBottom: '20px' }}>
            Staying informed shouldn't be a chore. But for most people, it is.
            Not because they don't care, but because finding news that actually
            matters to them takes more effort than it should.
          </p>
          <p style={{ ...s.body, marginBottom: '20px' }}>
            We built Resonance because we think that's worth fixing. News should
            come to you, shaped around what you genuinely care about, not what
            gets the most clicks or happens to surface on a front page.
          </p>
          <p style={s.body}>
            One quiet email, every morning. No infinite scroll. No manufactured
            urgency. Just the news that resonates with you.
          </p>
        </FadeIn>
      </section>

      {/* Team */}
      <div style={s.divider} />
      <section style={{ ...s.section, paddingTop: '80px' }}>
        <FadeIn>
          <div style={s.label}>Team</div>
          {['Kent Neureiter', 'Poshitha Upparapalli'].map(name => (
            <div key={name} style={{
              padding: '16px 0',
              borderBottom: '1px solid #e8e6e0',
              fontSize: '14px',
              fontFamily: 'sans-serif',
              color: '#444',
            }}>{name}</div>
          ))}
        </FadeIn>
      </section>

      {/* Footer */}
      <footer style={{
        maxWidth: '680px',
        margin: '0 auto',
        padding: '40px 48px',
        fontSize: '12px',
        fontFamily: 'sans-serif',
        color: '#bbb',
      }}>
        © 2026 Resonance
      </footer>

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        html { scroll-behavior: smooth; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input::placeholder { color: #bbb; }
      `}</style>

    </main>
  )
}