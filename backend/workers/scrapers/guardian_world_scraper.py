"""
guardian_world_scraper.py

Fetches the top 10 articles from Guardian's world section
and stores them in the world_candidates table.

Runs once per day as part of the daily pipeline, before world_ranker.py.

Run from backend/:
  python workers/scrapers/guardian_world_scraper.py
"""

import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
GUARDIAN_BASE_URL = "https://content.guardianapis.com/search"


def fetch_world_articles() -> list[dict]:
    """
    Fetches top 10 articles from Guardian's world section.
    """
    params = {
        "section":      "world",
        "show-fields":  "bodyText,trailText,byline",
        "page-size":    10,
        "order-by":     "newest",
        "api-key":      GUARDIAN_API_KEY
    }

    response = requests.get(GUARDIAN_BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    results = response.json().get("response", {}).get("results", [])
    print(f"  Fetched {len(results)} world articles from Guardian")
    return results


def save_candidates(articles: list[dict]) -> tuple[int, int]:
    """
    Saves articles to world_candidates table.
    Upserts on guardian_id so re-running is safe.
    Clears llm_rank so world_ranker re-ranks fresh each day.
    Returns (saved, skipped).
    """
    today = datetime.now(timezone.utc).date().isoformat()
    saved = 0
    skipped = 0

    for article in articles:
        guardian_id = article.get("id", "")
        fields = article.get("fields", {})

        row = {
            "guardian_id": guardian_id,
            "title":       article.get("webTitle", ""),
            "url":         article.get("webUrl", ""),
            "summary":     fields.get("trailText", ""),
            "body_text":   fields.get("bodyText", ""),
            "date":        today,
            "llm_rank":    None,  # will be filled by world_ranker.py
        }

        try:
            supabase.table("world_candidates").upsert(
                row, on_conflict="guardian_id"
            ).execute()
            saved += 1
        except Exception as e:
            print(f"  ⚠ Failed to save {guardian_id[:50]}: {e}")
            skipped += 1

    return saved, skipped


def run():
    print("\n" + "=" * 55)
    print("GUARDIAN WORLD SCRAPER")
    print("=" * 55 + "\n")

    articles = fetch_world_articles()

    if not articles:
        print("No articles returned. Exiting.")
        return

    saved, skipped = save_candidates(articles)

    print(f"\n{'=' * 55}")
    print(f"DONE — {saved} saved, {skipped} skipped")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()