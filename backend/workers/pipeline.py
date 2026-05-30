"""
pipeline.py

Orchestrates the full daily pipeline in order:
  1.  scrapers/Guardian.py         — Guardian articles
  2.  scrapers/verge.py            — The Verge
  3.  scrapers/ars_technica.py     — Ars Technica
  4.  scrapers/axios.py            — Axios
  5.  scrapers/bbc.py              — BBC
  6.  scrapers/eater.py            — Eater
  7.  scrapers/espn.py             — ESPN
  8.  scrapers/npr.py              — NPR
  9.  scrapers/techcrunch.py       — TechCrunch
  10. scrapers/jina.py             — fetch full text for all new articles
  11. embedders/articleembedder.py — embed all new articles
  12. ranking/clusterer.py         — assign cluster IDs
  13. ranking/ranker.py            — build briefings for all users
  14. scrapers/guardian_world_scraper.py — identify world candidates
  15. ranking/world_ranker.py      — pick top world article per user
  16. ranking/summarizer.py        — generate LLM summaries

Run from backend/:
  python workers/pipeline.py
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
        raise


def run():
    start = datetime.now(timezone.utc)

    print("\n" + "=" * 55)
    print(f"DAILY PIPELINE — {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    from workers.scrapers import Guardian
    from workers.scrapers import verge
    from workers.scrapers import ars_technica
    from workers.scrapers import axios
    from workers.scrapers import bbc
    from workers.scrapers import eater
    from workers.scrapers import espn
    from workers.scrapers import npr
    from workers.scrapers import techcrunch
    from workers.scrapers import jina
    from workers.embedders import articleembedder
    from workers.ranking import clusterer
    from workers.ranking import ranker
    from workers.scrapers import guardian_world_scraper
    from workers.ranking import world_ranker
    from workers.ranking import summarizer

    run_step("Guardian",               Guardian)
    run_step("The Verge",              verge)
    run_step("Ars Technica",           ars_technica)
    run_step("Axios",                  axios)
    run_step("BBC",                    bbc)
    run_step("Eater",                  eater)
    run_step("ESPN",                   espn)
    run_step("NPR",                    npr)
    run_step("TechCrunch",             techcrunch)
    run_step("Jina",                   jina)
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
