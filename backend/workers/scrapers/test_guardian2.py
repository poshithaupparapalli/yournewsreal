"""
scraper.py

Scrapes all Guardian articles published since the last scrape run
and stores them in Supabase. Handles pagination automatically.

Run manually with: python workers/scraper.py
Will eventually be run on a schedule (e.g. every morning at 6am).
"""

import os
import time
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
GUARDIAN_BASE_URL = "https://content.guardianapis.com/search"

# ─────────────────────────────────────────────────────────────
# TEST MODE — flip to False when running in production
# Limits scraper to 1 page of 50 articles so we don't flood
# the database while developing
TEST_MODE = True
TEST_PAGE_LIMIT = 1   # only fetch this many pages in test mode
TEST_PAGE_SIZE  = 50  # articles per page in test mode

# Production values — uncomment and use when TEST_MODE = False
# PAGE_SIZE = 200     # Guardian's maximum articles per page
# ─────────────────────────────────────────────────────────────


def get_last_scraped_at() -> str:
    """
    In TEST_MODE: always returns yesterday at noon UTC — hardcoded
    so every test run pulls the same predictable window of articles.

    In production: looks up the real last scrape time from Supabase
    so the scraper always picks up exactly where it left off.
    """
    if TEST_MODE:
        yesterday_noon = (datetime.now(timezone.utc) - timedelta(days=1)).replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        return yesterday_noon.isoformat()

    # Production — read the real last scrape timestamp from Supabase
    result = supabase.table("scrape_state").select("last_scraped_at").eq("id", 1).execute()

    if result.data:
        return result.data[0]["last_scraped_at"]

    # First ever production run — fall back to yesterday noon as well
    yesterday_noon = (datetime.now(timezone.utc) - timedelta(days=1)).replace(
        hour=12, minute=0, second=0, microsecond=0
    )
    return yesterday_noon.isoformat()


def update_last_scraped_at(timestamp: str):
    """
    Updates the scrape_state table with the current run time.
    Uses upsert so it works whether the row exists or not.
    """
    supabase.table("scrape_state").upsert({
        "id": 1,
        "last_scraped_at": timestamp
    }).execute()


def fetch_page(from_date: str, to_date: str, page: int) -> dict:
    """
    Fetches a single page of articles from the Guardian API.
    Returns the raw JSON response dict.
    """
    page_size = TEST_PAGE_SIZE if TEST_MODE else 200  # 200 is Guardian's max for prod

    params = {
        "from-date": from_date,
        "to-date": to_date,
        "show-fields": "bodyText,trailText,byline,thumbnail",
        "page-size": page_size,
        "page": page,
        "order-by": "newest",
        "api-key": GUARDIAN_API_KEY
    }

    response = requests.get(GUARDIAN_BASE_URL, params=params)
    response.raise_for_status()  # throws if the API returns an error
    return response.json()


def fetch_all_articles(from_date: str, to_date: str) -> list[dict]:
    """
    Paginates through Guardian results for the given time window.
    In TEST_MODE, stops after TEST_PAGE_LIMIT pages.
    In production, fetches every page until all articles are retrieved.
    Returns a flat list of article dicts.
    """
    print(f"  Fetching page 1...")
    data = fetch_page(from_date, to_date, page=1)
    response_body = data.get("response", {})

    total_pages = response_body.get("pages", 0)
    total_articles = response_body.get("total", 0)

    print(f"  Total articles available: {total_articles}")
    print(f"  Total pages available:    {total_pages}")

    if TEST_MODE:
        total_pages = min(total_pages, TEST_PAGE_LIMIT)
        print(f"  TEST MODE: capping at {total_pages} page(s) / ~{TEST_PAGE_SIZE} articles")

    if total_pages == 0:
        print("  No articles found for this time window.")
        return []

    all_articles = response_body.get("results", [])

    # Fetch remaining pages (skipped entirely in test mode since TEST_PAGE_LIMIT = 1)
    for page in range(2, total_pages + 1):
        print(f"  Fetching page {page}/{total_pages}...")
        data = fetch_page(from_date, to_date, page)
        articles = data.get("response", {}).get("results", [])
        all_articles.extend(articles)

        # Stay under Guardian's rate limit of 12 requests/sec
        time.sleep(0.1)

    print(f"  Fetched {len(all_articles)} articles total")
    return all_articles


def save_articles(articles: list[dict]) -> tuple[int, int]:
    """
    Saves articles to Supabase. Skips duplicates using the Guardian
    article ID as a unique key — safe to re-run without creating dupes.
    Returns (saved_count, skipped_count).
    """
    saved = 0
    skipped = 0

    for article in articles:
        guardian_id = article.get("id", "")
        fields = article.get("fields", {})

        body_text = fields.get("bodyText", "")

        # First 1500 chars — used for embedding so we don't send full articles to OpenAI
        # Roughly the first 2 paragraphs, which captures the who/what/why of the article
        body_preview = body_text[:1500] if body_text else ""

        row = {
            "guardian_id":   guardian_id,
            "title":         article.get("webTitle", ""),
            "url":           article.get("webUrl", ""),
            "published_at":  article.get("webPublicationDate", ""),
            "section":       article.get("sectionName", ""),
            "author":        fields.get("byline", ""),
            "summary":       fields.get("trailText", ""),
            "body_text":     body_text,
            "body_preview":  body_preview,   # first 1500 chars for embedding
            "source":        "guardian",
        }

        try:
            # upsert: insert if new, skip if guardian_id already exists
            supabase.table("articles").upsert(
                row, on_conflict="guardian_id"
            ).execute()
            saved += 1
        except Exception as e:
            print(f"  ⚠ Failed to save {guardian_id}: {e}")
            skipped += 1

    return saved, skipped


def run():
    """
    Main scrape cycle:
    1. Get the time window (last scrape → now)
    2. Fetch all articles in that window from Guardian
    3. Save to Supabase
    4. Update last_scraped_at so next run picks up from here
    """
    print("\n" + "=" * 60)
    print("GUARDIAN SCRAPER")
    print("=" * 60)

    from_date = get_last_scraped_at()
    to_date = datetime.now(timezone.utc).isoformat()

    print(f"\nTime window:")
    print(f"  From: {from_date}")
    print(f"  To:   {to_date}\n")

    articles = fetch_all_articles(from_date, to_date)

    if not articles:
        print("\nNothing to save. Exiting.")
        return

    print(f"\nSaving to Supabase...")
    saved, skipped = save_articles(articles)
    print(f"  Saved:   {saved}")
    print(f"  Skipped: {skipped}")

    update_last_scraped_at(to_date)
    print(f"\nUpdated last_scraped_at → {to_date}")

    print("\n" + "=" * 60)
    print(f"DONE — {saved} new articles in Supabase")
    print("=" * 60)


if __name__ == "__main__":
    run()