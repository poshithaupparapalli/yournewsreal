"""
pipeline.py

Runs once daily at 7am EST.
Assumes scraper_pipeline.py has already been collecting article links
throughout the day via RSS feeds.

Steps:
  0. truncate_daily_tables()      — clear briefings, world_candidates, articles
  1. test_guardian2.py            — fetch Guardian articles → articles table
  2. jina.py                      — fetch full text for RSS links → articles table
  3. embedders/articleembedder.py — embed all new articles
  4. ranking/clusterer.py         — assign cluster IDs
  5. ranking/ranker.py            — build per-user briefings (interests + learning)
  6. scrapers/guardian_world_scraper.py — fetch world article candidates
  7. ranking/world_ranker.py      — pick top world article per user → briefings
  8. ranking/summarizer.py        — generate LLM summaries for all briefing articles
  9. truncate_article_links()     — clear article_links now that pipeline is done

Run from backend/:
  python workers/pipeline.py
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reset_tables():
    from database.connection import supabase

    print(f"\n{'─' * 55}")
    print("STEP: Reset Tables (briefings, world_candidates, articles)")
    print(f"{'─' * 55}")
    try:
        supabase.rpc("truncate_daily_tables").execute()
        print("✓ Reset complete")
    except Exception as e:
        print(f"✗ Failed to reset tables: {e}")
        raise


def clear_article_links():
    from database.connection import supabase

    print(f"\n{'─' * 55}")
    print("STEP: Clear Article Links")
    print(f"{'─' * 55}")
    try:
        supabase.rpc("truncate_article_links").execute()
        print("✓ article_links cleared")
    except Exception as e:
        print(f"✗ Failed to clear article_links: {e}")
        raise


def run_step(name: str, module):
    print(f"\n{'─' * 55}")
    print(f"STEP: {name}")
    print(f"{'─' * 55}")
    try:
        module.run()
        print(f"✓ {name} complete")
    except Exception as e:
        print(f"✗ {name} failed: {e}")
        raise


def run():
    start = datetime.now(timezone.utc)

    print("\n" + "=" * 55)
    print(f"DAILY PIPELINE — {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    from workers.scrapers import test_guardian2
    from workers.scrapers import jina
    from workers.embedders import articleembedder
    from workers.ranking import clusterer
    from workers.ranking import ranker
    from workers.scrapers import guardian_world_scraper
    from workers.ranking import world_ranker
    from workers.ranking import summarizer

    reset_tables()
    run_step("Guardian Scraper",       test_guardian2)
    run_step("Jina Fetcher",           jina)
    run_step("Article Embedder",       articleembedder)
    run_step("Clusterer",              clusterer)
    run_step("Ranker",                 ranker)
    run_step("Guardian World Scraper", guardian_world_scraper)
    run_step("World Ranker",           world_ranker)
    run_step("Summarizer",             summarizer)
    clear_article_links()

    elapsed = (datetime.now(timezone.utc) - start).seconds
    print(f"\n{'=' * 55}")
    print(f"PIPELINE COMPLETE — {elapsed}s")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()