"""
pipeline.py

Orchestrates the full daily pipeline in order:
  1. scraper.py         — fetch Guardian articles
  2. jina_fetcher.py    — fetch full text for RSS links
  3. article_embedder.py — embed all new articles
  4. clusterer.py       — assign cluster IDs
  5. ranker.py          — build briefings for all users
  6. emailer.py         — send briefing emails

Run from backend/:
  python workers/pipeline.py

This is what Railway calls each morning at 7am UTC.
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_step(name: str, module):
    print(f"\n{'─' * 55}")
    print(f"STEP: {name}")
    print(f"{'─' * 55}")
    try:
        module.run()
        print(f"✓ {name} complete")
    except Exception as e:
        print(f"✗ {name} failed: {e}")
        raise  # stop pipeline if any step fails


def run():
    start = datetime.now(timezone.utc)

    print("\n" + "=" * 55)
    print(f"DAILY PIPELINE — {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    # Import each worker module
    from workers import scraper
    from workers import jina_fetcher
    from workers.embedders import article_embedder
    from workers import clusterer
    from workers import ranker
    from workers import emailer

    run_step("Guardian Scraper",   scraper)
    run_step("Jina Fetcher",       jina_fetcher)
    run_step("Article Embedder",   article_embedder)
    run_step("Clusterer",          clusterer)
    run_step("Ranker",             ranker)
    run_step("Emailer",            emailer)

    elapsed = (datetime.now(timezone.utc) - start).seconds
    print(f"\n{'=' * 55}")
    print(f"PIPELINE COMPLETE — {elapsed}s")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()