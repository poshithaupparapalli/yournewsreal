"""
pipeline.py

Orchestrates the full daily pipeline in order:
  1. scrapers/scraper.py      — fetch Guardian articles
  2. scrapers/jina.py         — fetch full text for RSS links
  3. embedders/articleembedder.py — embed all new articles
  4. ranking/clusterer.py     — assign cluster IDs
  5. ranking/ranker.py        — build briefings for all users
  6. ranking/summarizer.py    — generate LLM summaries for briefing articles
  7. emailer.py               — send briefing emails

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

    from workers.scrapers import scraper
    from workers.scrapers import jina
    from workers.embedders import articleembedder
    from workers.ranking import clusterer
    from workers.ranking import ranker
    from workers.ranking import summarizer
    from workers import emailer

    run_step("Guardian Scraper",   scraper)
    run_step("Jina Fetcher",       jina)
    run_step("Article Embedder",   articleembedder)
    run_step("Clusterer",          clusterer)
    run_step("Ranker",             ranker)
    run_step("Summarizer",         summarizer)
    run_step("Emailer",            emailer)

    elapsed = (datetime.now(timezone.utc) - start).seconds
    print(f"\n{'=' * 55}")
    print(f"PIPELINE COMPLETE — {elapsed}s")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()