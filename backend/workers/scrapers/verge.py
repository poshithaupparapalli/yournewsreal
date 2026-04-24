import os
import sys
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

# ─────────────────────────────────────────────────────────────
# OUTLET CONFIG — only thing that changes between outlet files
# ─────────────────────────────────────────────────────────────
OUTLET_NAME = "verge"
RSS_URL     = "https://www.theverge.com/rss/index.xml"

# How far back to look for articles (should match how often this scraper runs)
# e.g. if running every 2 hours, look back 2.5 hours to avoid gaps
LOOKBACK_HOURS = 2.5

# Browser-like headers so RSS servers don't block us
RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}
# ─────────────────────────────────────────────────────────────


def fetch_rss_entries() -> list[dict]:
    """
    Fetches the RSS feed and returns all entries published
    within the lookback window as a list of dicts.
    """
    try:
        response = requests.get(RSS_URL, headers=RSS_HEADERS, timeout=15)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"  [{OUTLET_NAME}] RSS fetch failed: {e}")
        return []

    window_start = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    entries = []

    for entry in feed.entries:
        url   = entry.get("link", "").strip()
        title = entry.get("title", "").strip()

        if not url or not title:
            continue

        # Parse publish date
        published_at = None
        pp = entry.get("published_parsed")
        if pp:
            try:
                published_at = datetime(*pp[:6], tzinfo=timezone.utc)
            except Exception:
                pass

        # Filter to lookback window — if no date, include it to be safe
        if published_at and published_at < window_start:
            continue

        entries.append({
            "url":          url,
            "title":        title,
            "source":       OUTLET_NAME,
            "published_at": published_at.isoformat() if published_at else None,
            "summary":      entry.get("summary", "")[:500] if entry.get("summary") else None,
            "fetched":      False,
        })

    return entries


def save_links(entries: list[dict]) -> tuple[int, int]:
    """
    Saves article links to Supabase.
    The UNIQUE constraint on url handles deduplication automatically —
    if the URL already exists, the upsert skips it cleanly.
    Returns (saved, skipped) counts.
    """
    saved   = 0
    skipped = 0

    for entry in entries:
        try:
            result = supabase.table("article_links").upsert(
                entry, on_conflict="url", ignore_duplicates=True
            ).execute()

            # If no rows were affected, it was a duplicate
            if result.data:
                saved += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"  ⚠ Failed to save {entry['url'][:60]}: {e}")
            skipped += 1

    return saved, skipped


def run():
    print(f"\n{'=' * 55}")
    print(f"RSS SCRAPER — {OUTLET_NAME.upper()}")
    print(f"Lookback: {LOOKBACK_HOURS} hours")
    print(f"{'=' * 55}")

    entries = fetch_rss_entries()

    if not entries:
        print("\nNo new entries found. Exiting.")
        return

    print(f"\nFound {len(entries)} entries in window")
    print(f"Saving to article_links table...")

    saved, skipped = save_links(entries)

    print(f"\n{'=' * 55}")
    print(f"DONE — {saved} new links saved, {skipped} already existed")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()