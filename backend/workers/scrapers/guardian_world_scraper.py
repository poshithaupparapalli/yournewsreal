"""
guardian_world_scraper.py

Reads Guardian world section articles already in the articles table
and copies them into world_candidates for the world_ranker to use.

No API calls needed — just queries what the main scraper already saved.

Run from backend/:
  python workers/scrapers/guardian_world_scraper.py
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()


def fetch_world_articles_from_db() -> list[dict]:
    """
    Fetches today's Guardian world section articles from the articles table.
    These were already saved by the main scraper — no API call needed.
    """
    today = datetime.now(timezone.utc).date().isoformat()

    result = (
        supabase.table("articles")
        .select("id, guardian_id, title, url, summary, body_text, published_at")
        .eq("source", "guardian")
        .eq("section", "World news")
        .gte("scraped_at", today)
        .order("scraped_at", desc=True)
        .limit(20)
        .execute()
    )

    print(f"  Found {len(result.data)} Guardian world articles in articles table")
    return result.data


def save_to_world_candidates(articles: list[dict]) -> tuple[int, int]:
    """
    Copies world articles into the world_candidates table.
    Upserts on guardian_id so re-running is safe.
    Resets llm_rank so world_ranker re-ranks fresh each day.
    Returns (saved, skipped).
    """
    today = datetime.now(timezone.utc).date().isoformat()
    saved = 0
    skipped = 0

    for article in articles:
        row = {
            "guardian_id": article["guardian_id"],
            "title":       article["title"],
            "url":         article["url"],
            "summary":     article.get("summary", ""),
            "body_text":   article.get("body_text", ""),
            "date":        today,
            "llm_rank":    None,  # filled by world_ranker.py
        }

        try:
            supabase.table("world_candidates").upsert(
                row, on_conflict="guardian_id"
            ).execute()
            saved += 1
        except Exception as e:
            print(f"  ⚠ Failed to save {article.get('guardian_id', '')[:50]}: {e}")
            skipped += 1

    return saved, skipped


def run():
    print("\n" + "=" * 55)
    print("GUARDIAN WORLD SCRAPER")
    print("=" * 55 + "\n")

    articles = fetch_world_articles_from_db()

    if not articles:
        print("No Guardian world articles found in articles table for today.")
        print("Make sure the main Guardian scraper has run first.")
        return

    saved, skipped = save_to_world_candidates(articles)

    print(f"\n{'=' * 55}")
    print(f"DONE — {saved} saved to world_candidates, {skipped} skipped")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()