"""
pipeline.py

Runs once daily at 7am UTC.
Assumes scraper_pipeline.py has already been collecting article links
throughout the day via RSS feeds.

Steps:
  0. Reset tables                 — clear article_links, articles, briefings, world_candidates
  1. test_guardian2.py            — fetch Guardian articles → articles table
  2. jina.py                      — fetch full text for RSS links → articles table
  3. embedders/articleembedder.py — embed all new articles
  4. ranking/clusterer.py         — assign cluster IDs
  5. ranking/ranker.py            — build per-user briefings (interests + learning)
  6. scrapers/guardian_world_scraper.py — fetch world article candidates
  7. ranking/world_ranker.py      — pick top world article per user → briefings
  8. ranking/summarizer.py        — generate LLM summaries for all briefing articles

Run from backend/:
  python workers/pipeline.py
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reset_tables():
    """
    Clears all daily working tables so users never see
    the same articles two days in a row.
    Tables cleared: article_links, articles, briefings, world_candidates
    Users and user embeddings are never touched.
    """
    from database.connection import supabase

    tables = ["briefings", "world_candidates", "articles", "article_links"]

    print(f"\n{'─' * 55}")
    print("STEP: Reset Tables")
    print(f"{'─' * 55}")

    for table in tables:
        try:
            # Delete all rows — neq is a workaround since Supabase
            # doesn't allow a bare delete() without a filter
            supabase.table(table).delete().neq("id", 0).execute()
            print(f"  ✓ {table} cleared")
        except Exception as e:
            print(f"  ✗ Failed to clear {table}: {e}")
            raise

    print("✓ Reset complete")


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

    elapsed = (datetime.now(timezone.utc) - start).seconds
    print(f"\n{'=' * 55}")
    print(f"PIPELINE COMPLETE — {elapsed}s")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()