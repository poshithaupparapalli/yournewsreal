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
      backgroundColor: '#c6c6c6',
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
      backgroundColor: '#f2f2f2',
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
    h1: {
      fontSize: 'clamp(48px, 7vw, 84px)',
      fontWeight: '400',
      lineHeight: '1.05',
      letterSpacing: '-0.02em',
      marginBottom: '32px',
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

      {/* Hero */}
      <section style={{ ...s.section, paddingTop: '200px', paddingBottom: '160px' }}>
        <div style={{
          fontSize: '11px',
          fontFamily: 'sans-serif',
          color: '#dedede',
          letterSpacing: '0.1em',
          marginBottom: '40px',
        }}>
          Your morning briefing
        </div>
        <h1 style={s.h1}>
          News that<br />resonates.
        </h1>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="email"
            placeholder="your@email.com"
            style={{
              border: 'none',
              borderBottom: '1px solid #aaa',
              background: 'transparent',
              padding: '10px 0',
              fontSize: '15px',
              fontFamily: 'sans-serif',
              width: '240px',
              outline: 'none',
              color: '#1a1a1a',
            }}
          />
          <button style={{
            background: 'transparent',
            color: '#1a1a1a',
            border: '1px solid #1a1a1a',
            padding: '10px 24px',
            fontSize: '13px',
            fontFamily: 'sans-serif',
            letterSpacing: '0.04em',
            cursor: 'pointer',
          }}>
            join waitlist
          </button>
        </div>

        {/* Scroll hint */}
        <div style={{
          marginTop: '80px',
          fontSize: '12px',
          fontFamily: 'sans-serif',
          color: '#bbb',
          letterSpacing: '0.06em',
        }}>
          Scroll to see how it works ↓
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
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

        {/* Onboarding mockup */}
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

        {/* Sources → articles visual */}
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
              {['guardian', 'techcrunch', 'bbc', 'axios', 'the verge', 'ars technica', 'npr', 'al jazeera', 'eater', 'espn'].map(s => (
                <span key={s} style={{
                  fontSize: '11px',
                  fontFamily: 'sans-serif',
                  color: '#666',
                  background: '#f5f4f0',
                  border: '1px solid #e8e6e0',
                  padding: '4px 10px',
                  borderRadius: '2px',
                  letterSpacing: '0.04em',
                }}>
                  {s}
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

        {/* Briefing mockup */}
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

/*
import Image from "next/image";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={100}
          height={20}
          priority
        />
        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            To get started, edit the page.js file.
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            Looking for a starting point or more instructions? Head over to{" "}
            <a
              href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
              className="font-medium text-zinc-950 dark:text-zinc-50"
            >
              Templates
            </a>{" "}
            or the{" "}
            <a
              href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
              className="font-medium text-zinc-950 dark:text-zinc-50"
            >
              Learning
            </a>{" "}
            center.
          </p>
        </div>
        <div className="flex flex-col gap-4 text-base font-medium sm:flex-row">
          <a
            className="flex h-12 w-full items-center justify-center gap-2 rounded-full bg-foreground px-5 text-background transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc] md:w-[158px]"
            href="https://vercel.com/new?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Image
              className="dark:invert"
              src="/vercel.svg"
              alt="Vercel logomark"
              width={16}
              height={16}
            />
            Deploy Now
          </a>
          <a
            className="flex h-12 w-full items-center justify-center rounded-full border border-solid border-black/[.08] px-5 transition-colors hover:border-transparent hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a] md:w-[158px]"
            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            Documentation
          </a>
        </div>
      </main>
    </div>
  );
}
*/