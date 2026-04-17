"""
daily_scraper.py

Pulls up to 20 articles per outlet published in the last 20 hours
(noon yesterday → 8am today). Uses Jina Reader for full text.
Skips articles where Jina fails. Embeds everything. Saves to JSON.

Run: python3 daily_scraper.py
"""

import requests
import feedparser
import json
import os
import time
import hashlib
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")

# ── Config ────────────────────────────────────────────
MAX_PER_OUTLET = 20
MIN_BODY_CHARS = 500   # skip articles with no real content
JINA_TIMEOUT   = 25    # seconds per article
JINA_DELAY     = 0.5   # seconds between Jina calls (rate limit)

# ── Time window ───────────────────────────────────────
# noon yesterday → 8am today (20 hours)
_now = datetime.now(timezone.utc)
_today_8am = _now.replace(hour=8, minute=0, second=0, microsecond=0)
WINDOW_END   = _today_8am if _now >= _today_8am else _today_8am - timedelta(days=1)
WINDOW_START = WINDOW_END - timedelta(hours=20)

# ── RSS outlets ───────────────────────────────────────
RSS_OUTLETS = [
    {"name": "TechCrunch",   "rss": "https://techcrunch.com/feed/"},
    {"name": "The Verge",    "rss": "https://www.theverge.com/rss/index.xml"},
    {"name": "Ars Technica", "rss": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "BBC News",     "rss": "https://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "NPR",          "rss": "https://feeds.npr.org/1001/rss.xml"},
    {"name": "ESPN",         "rss": "https://www.espn.com/espn/rss/news"},
    {"name": "Eater",        "rss": "https://www.eater.com/rss/index.xml"},
    # Wired, Bloomberg, STAT News: paywalled — Jina can't get full text
    # Reuters, AP News: no working RSS feed available
]

# Guardian API pulls full text directly — no Jina needed
GUARDIAN_SECTIONS = [
    "technology", "science", "business", "world",
    "environment", "sport", "culture", "us-news",
]


# ─────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────

def article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def in_window(published_parsed) -> bool:
    """Check if a feedparser time struct falls within the scrape window."""
    if not published_parsed:
        return True  # no date → assume recent, include it
    try:
        pub = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        return WINDOW_START <= pub <= WINDOW_END
    except Exception:
        return True


def jina_fetch(url: str) -> str | None:
    """Fetch full article text via Jina Reader. Returns None on failure."""
    try:
        resp = requests.get(
            f"https://r.jina.ai/{url}",
            timeout=JINA_TIMEOUT,
            headers={"Accept": "text/plain"},
        )
        text = resp.text.strip()
        if len(text) >= MIN_BODY_CHARS and not _is_blocked(text):
            return text
    except Exception:
        pass
    return None


def _is_blocked(text: str) -> bool:
    signals = ["enable javascript", "access denied", "cloudflare",
               "bot activity", "unusual traffic", "please enable"]
    t = text.lower()
    return any(s in t for s in signals)


def embed_articles(articles: list[dict]) -> list[dict]:
    """Add an 'embedding' field to each article using a local model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  [embed] sentence-transformers not installed — skipping embeddings")
        print("  Run: pip install sentence-transformers")
        for a in articles:
            a["embedding"] = []
        return articles

    print(f"\n[embed] Loading model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [f"{a['title']}. {a['body'][:1000]}" for a in articles]
    print(f"[embed] Embedding {len(texts)} articles...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

    for article, emb in zip(articles, embeddings):
        article["embedding"] = emb.tolist()

    return articles


# ─────────────────────────────────────────────────────
# SCRAPERS
# ─────────────────────────────────────────────────────

RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}

def scrape_rss_outlet(outlet: dict) -> list[dict]:
    """RSS → filter by time window → Jina for full text."""
    name = outlet["name"]
    articles = []

    try:
        resp = requests.get(outlet["rss"], headers=RSS_HEADERS, timeout=15)
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  [{name}] RSS fetch failed: {e}")
        return []

    entries = feed.entries[:MAX_PER_OUTLET * 2]  # grab extra in case some fail

    in_window_entries = [e for e in entries if in_window(e.get("published_parsed"))]
    in_window_entries = in_window_entries[:MAX_PER_OUTLET]

    print(f"  [{name}] {len(in_window_entries)} articles in window — fetching full text via Jina...")

    for entry in in_window_entries:
        url = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not url or not title:
            continue

        body = jina_fetch(url)
        time.sleep(JINA_DELAY)

        if body is None:
            print(f"    ✗ skip (no full text): {title[:60]}")
            continue

        pub_date = ""
        if entry.get("published_parsed"):
            try:
                pub_date = datetime(*entry.published_parsed[:6],
                                    tzinfo=timezone.utc).isoformat()
            except Exception:
                pass

        articles.append({
            "id":           article_id(url),
            "title":        title,
            "url":          url,
            "outlet":       name,
            "published_at": pub_date,
            "body":         body,
            "word_count":   len(body.split()),
            "scraped_at":   datetime.now(timezone.utc).isoformat(),
        })
        print(f"    ✓ {title[:60]}")

    return articles


def scrape_guardian_section(section: str) -> list[dict]:
    """Guardian API → full text included, no Jina needed."""
    articles = []

    params = {
        "section":      section,
        "show-fields":  "bodyText,byline",
        "page-size":    MAX_PER_OUTLET,
        "order-by":     "newest",
        "from-date":    WINDOW_START.strftime("%Y-%m-%d"),
        "api-key":      GUARDIAN_API_KEY,
    }

    try:
        resp = requests.get("https://content.guardianapis.com/search",
                            params=params, timeout=15)
        results = resp.json().get("response", {}).get("results", [])
    except Exception as e:
        print(f"  [Guardian/{section}] API failed: {e}")
        return []

    print(f"  [Guardian/{section}] {len(results)} articles")

    for item in results:
        body = item.get("fields", {}).get("bodyText", "").strip()
        if len(body) < MIN_BODY_CHARS:
            continue

        url   = item.get("webUrl", "")
        title = item.get("webTitle", "").strip()

        articles.append({
            "id":           article_id(url),
            "title":        title,
            "url":          url,
            "outlet":       f"The Guardian",
            "section":      section,
            "published_at": item.get("webPublicationDate", ""),
            "body":         body,
            "word_count":   len(body.split()),
            "scraped_at":   datetime.now(timezone.utc).isoformat(),
        })
        print(f"    ✓ {title[:60]}")

    return articles


# ─────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("DAILY SCRAPER")
    print(f"Window: {WINDOW_START.strftime('%b %d %H:%M')} UTC → "
          f"{WINDOW_END.strftime('%b %d %H:%M')} UTC")
    print("=" * 60)

    all_articles = []

    # RSS outlets
    print("\n── RSS OUTLETS ──────────────────────────────────")
    for outlet in RSS_OUTLETS:
        articles = scrape_rss_outlet(outlet)
        all_articles.extend(articles)
        print(f"  [{outlet['name']}] collected {len(articles)}")

    # Guardian API
    print("\n── GUARDIAN API ─────────────────────────────────")
    for section in GUARDIAN_SECTIONS:
        articles = scrape_guardian_section(section)
        all_articles.extend(articles)

    # Deduplicate by URL
    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    print(f"\n── TOTALS ───────────────────────────────────────")
    print(f"  Raw articles:   {len(all_articles)}")
    print(f"  After URL dedup: {len(unique)}")

    # Embed
    unique = embed_articles(unique)

    # Save
    os.makedirs("output", exist_ok=True)
    date_str  = datetime.now().strftime("%Y-%m-%d")
    out_path  = f"output/articles_{date_str}.json"

    with open(out_path, "w") as f:
        json.dump({
            "scraped_at":    datetime.now(timezone.utc).isoformat(),
            "window_start":  WINDOW_START.isoformat(),
            "window_end":    WINDOW_END.isoformat(),
            "total_articles": len(unique),
            "articles":      unique,
        }, f, indent=2)

    print(f"\n  Saved → {out_path}")
    print(f"  {len(unique)} articles ready\n")


if __name__ == "__main__":
    main()
