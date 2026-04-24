"""
daily_scraper.py
────────────────
THE BIG PICTURE
───────────────
Every day at 8am we want a list of ~300 articles from across the web,
with the full text of each article, ready to be ranked against each user's interests.

The pipeline has 3 stages:
  1. DISCOVER  — find article URLs published in the last 20 hours
  2. FETCH     — get the full text of each article (this is where Jina comes in)
  3. SAVE      — store the articles in Supabase

WHAT IS JINA?
─────────────
Normally if you try to fetch a news article with Python's requests library,
you get back a wall of HTML — nav bars, ads, sidebars, cookie banners, scripts.
Extracting just the article text from that is messy and breaks every time a site
redesigns.

Jina Reader solves this. You call:
  https://r.jina.ai/<any article URL>

Jina's server fetches that page using a real headless browser (like Chrome running
on their servers), waits for the JavaScript to load, then strips out all the noise
and returns clean markdown — just the title, author, date, and article body.

You send:  https://r.jina.ai/https://techcrunch.com/2026/04/17/some-article
You get back:
  Title: Some Article
  Author: Jane Doe
  Body: The actual article text here...

It's like asking someone to read a webpage for you and summarise just the content.

HOW WE GET THE ARTICLE URLS
────────────────────────────
Most news sites publish an RSS feed — a simple XML file that lists their latest
articles with titles, URLs, and publish dates. It's designed for exactly this use
case (news readers, aggregators). We parse it with feedparser.

For The Guardian we use their official API instead, which gives us the full article
text directly — no Jina needed.

RUN THIS FILE
─────────────
  python3 daily_scraper.py

For testing it's limited to TEST_LIMIT articles per outlet.
Change TEST_LIMIT = None to remove the limit for production.
"""

import requests
import feedparser
import time
import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Add the parent directory to path so we can import from database/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()
# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

# For testing: only fetch this many articles per outlet so we don't hammer APIs.
# Set to None to remove the limit for production.
TEST_LIMIT = None

# Jina won't always succeed. We only keep an article if Jina returned at least
# this many characters of body text. Anything shorter is probably a blocked page
# or a redirect, not a real article.
MIN_BODY_CHARS = 500

# How long to wait for Jina to respond before giving up on an article (seconds).
JINA_TIMEOUT = 25

# Pause between Jina calls so we don't hit their rate limit.
# At 0.5s, fetching 100 articles takes ~50 seconds.
JINA_DELAY = 0.5

# ─────────────────────────────────────────────────────────────────────────────
# TIME WINDOW
# ─────────────────────────────────────────────────────────────────────────────
# We only want articles from the last 20 hours: noon yesterday → 8am today.
# This way each daily run captures overnight news without double-counting.
# When run at 8am:  window = yesterday 12:00 → today 08:00
# When run later:   same window (we don't slide it forward)

_now = datetime.now(timezone.utc)
WINDOW_END   = _now
WINDOW_START = _now - timedelta(hours=24)

# ─────────────────────────────────────────────────────────────────────────────
# OUTLETS — RSS feeds
# ─────────────────────────────────────────────────────────────────────────────
# Each outlet just needs a name and an RSS feed URL.
# We tested all of these — Jina can successfully fetch full text from them.
# Removed: Wired, Bloomberg, STAT News (paywalled), Reuters/AP (no working RSS)

RSS_OUTLETS = [
    {"name": "TechCrunch",   "rss": "https://techcrunch.com/feed/"},
    {"name": "The Verge",    "rss": "https://www.theverge.com/rss/index.xml"},
    {"name": "Ars Technica", "rss": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "BBC News",     "rss": "https://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "NPR",          "rss": "https://feeds.npr.org/1001/rss.xml"},
    {"name": "ESPN",         "rss": "https://www.espn.com/espn/rss/news"},
    {"name": "Eater",        "rss": "https://www.eater.com/rss/index.xml"},
]

# Browser-like headers so RSS servers don't block us
RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: CHECK IF JINA GOT BLOCKED
# ─────────────────────────────────────────────────────────────────────────────

def jina_was_blocked(text: str) -> bool:
    """
    Sometimes Jina fetches the page but the site served a bot-block page instead
    of the real article. We detect this by looking for phrases that appear on
    bot-block pages but never in real articles.
    """
    block_phrases = [
        "enable javascript",  # JS-required gate pages
        "access denied",      # explicit blocks
        "cloudflare",         # Cloudflare bot protection
        "bot activity",       # generic bot block
        "unusual traffic",    # Google-style bot detection
        "please enable",      # JS prompt
    ]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in block_phrases)


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: FETCH FULL TEXT VIA JINA
# ─────────────────────────────────────────────────────────────────────────────

def fetch_with_jina(article_url: str) -> str | None:
    """
    Takes a URL like https://techcrunch.com/2026/04/17/some-article
    Calls Jina:       https://r.jina.ai/https://techcrunch.com/2026/04/17/some-article

    Jina fetches the page with a headless browser, strips the HTML noise,
    and returns clean markdown text with just the article content.

    Returns the body text if successful, or None if:
    - Jina timed out (site too slow)
    - The page was bot-blocked
    - The text is too short to be a real article (< MIN_BODY_CHARS characters)
    """
    jina_url = f"https://r.jina.ai/{article_url}"

    try:
        response = requests.get(
            jina_url,
            timeout=JINA_TIMEOUT,
            headers={"Accept": "text/plain"},  # ask for plain text, not HTML
        )
        body = response.text.strip()

        # Reject if too short — probably a redirect or error page
        if len(body) < MIN_BODY_CHARS:
            return None

        # Reject if it looks like a bot-block page
        if jina_was_blocked(body):
            return None

        return body

    except requests.exceptions.Timeout:
        return None  # Jina took too long — skip this article
    except Exception:
        return None  # Any other network error — skip


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 + 2 COMBINED: RSS OUTLET
# ─────────────────────────────────────────────────────────────────────────────

def scrape_rss_outlet(outlet: dict) -> list[dict]:
    """
    For a given RSS outlet:
      1. Fetch the RSS feed (a list of recent articles with URLs + dates)
      2. Filter to only articles published in our 20-hour window
      3. For each article URL, call Jina to get the full text
      4. Return successfully fetched articles as a list of dicts
    """
    name = outlet["name"]
    articles = []

    # ── Step 1: Fetch and parse the RSS feed ──────────────────────────────────
    # We use requests (not feedparser directly) because feedparser's built-in
    # fetcher gets blocked by some servers. Requests with browser headers works.
    try:
        rss_response = requests.get(outlet["rss"], headers=RSS_HEADERS, timeout=15)
        feed = feedparser.parse(rss_response.content)
    except Exception as e:
        print(f"  [{name}] RSS fetch failed: {e}")
        return []

    # Apply test limit — grab extra entries in case some fail the time filter
    entries = feed.entries[: (TEST_LIMIT or 20) * 3]

    # ── Step 2: Filter by time window ────────────────────────────────────────
    # RSS entries have a published_parsed field (a time.struct_time in UTC).
    # We convert it to a timezone-aware datetime and check if it's in our window.
    # If an entry has no date, we include it (assume it's recent).
    def in_window(entry) -> bool:
        pp = entry.get("published_parsed")
        if not pp:
            return True
        try:
            pub = datetime(*pp[:6], tzinfo=timezone.utc)
            return WINDOW_START <= pub <= WINDOW_END
        except Exception:
            return True

    in_window_entries = [e for e in entries if in_window(e)]
    if TEST_LIMIT:
        in_window_entries = in_window_entries[:TEST_LIMIT]

    print(f"  [{name}] {len(in_window_entries)} articles in window — fetching full text via Jina...")

    # ── Step 3: Fetch full text for each article via Jina ────────────────────
    for entry in in_window_entries:
        url   = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not url or not title:
            continue

        # This is the core Jina call — see fetch_with_jina() above
        body = fetch_with_jina(url)

        # Pause between calls — Jina has a rate limit
        time.sleep(JINA_DELAY)

        if body is None:
            print(f"    ✗ skip (Jina failed): {title[:60]}")
            continue

        # Parse the publish date into a clean ISO string
        published_at = None
        if entry.get("published_parsed"):
            try:
                published_at = datetime(
                    *entry.published_parsed[:6], tzinfo=timezone.utc
                ).isoformat()
            except Exception:
                pass

        articles.append({
            "title":        title,
            "url":          url,
            "source":       name.lower().replace(" ", "_"),  # e.g. "bbc_news"
            "section":      None,
            "author":       None,
            "summary":      entry.get("summary", "")[:500] if entry.get("summary") else None,
            "body_text":    body,
            "body_preview": body[:300],
            "published_at": published_at,
            "guardian_id":  url,  # no Guardian ID for RSS — use URL as unique identifier
        })
        print(f"    ✓ {title[:65]}")

    return articles
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: SAVE TO SUPABASE
# ─────────────────────────────────────────────────────────────────────────────

def save_to_supabase(articles: list[dict]) -> int:
    """
    Insert articles into the Supabase `articles` table.

    Guardian articles use upsert on guardian_id (that column has a UNIQUE constraint).
    RSS articles use plain insert — if the same URL was already saved from a previous
    run, Supabase will throw a duplicate error and we skip it.

    Returns the number of articles successfully saved.
    """
    if not articles:
        return 0

    saved = 0
    for article in articles:
        try:
            # Both Guardian and RSS articles now have a unique guardian_id
            # (Guardian uses their own ID, RSS uses the article URL)
            supabase.table("articles").upsert(
                article, on_conflict="guardian_id"
            ).execute()
            saved += 1
        except Exception as e:
            err = str(e)
            if "duplicate" in err.lower() or "unique" in err.lower():
                pass  # already in DB from a previous run, that's fine
            else:
                print(f"    ✗ DB error for '{article['title'][:40]}': {e}")

    return saved


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — runs the full pipeline
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 65)
    print("DAILY SCRAPER")
    if TEST_LIMIT:
        print(f"TEST MODE — {TEST_LIMIT} articles per outlet")
    print(f"Window: {WINDOW_START.strftime('%b %d %H:%M')} UTC → {WINDOW_END.strftime('%b %d %H:%M')} UTC")
    print("=" * 65)

    all_articles = []

    # ── Stage 1+2: Scrape RSS outlets ─────────────────────────────────────────
    print("\n── RSS OUTLETS ──────────────────────────────────────────────────")
    for outlet in RSS_OUTLETS:
        articles = scrape_rss_outlet(outlet)
        all_articles.extend(articles)
        print(f"  [{outlet['name']}] collected {len(articles)}\n")

    # Guardian is handled separately by workers/scraper.py

    # ── Deduplicate by URL ────────────────────────────────────────────────────
    # In rare cases the same article appears in multiple RSS feeds or Guardian
    # sections. We remove duplicates so we don't insert the same row twice.
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article["url"] not in seen_urls:
            seen_urls.add(article["url"])
            unique_articles.append(article)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n── TOTALS ───────────────────────────────────────────────────────")
    print(f"  Scraped:          {len(all_articles)}")
    print(f"  After URL dedup:  {len(unique_articles)}")

    # ── Stage 3: Save to Supabase ─────────────────────────────────────────────
    print(f"\n── SAVING TO SUPABASE ───────────────────────────────────────────")
    saved = save_to_supabase(unique_articles)
    print(f"  Saved: {saved} / {len(unique_articles)} articles")
    print(f"\nDone.\n")


if __name__ == "__main__":
    main()
