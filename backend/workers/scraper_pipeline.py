"""
scraper_pipeline.py

Runs every 30 minutes to collect fresh articles from all sources.
Only scrapes — no embedding, ranking, or summarizing.
Those run once daily in pipeline.py at 7am.

Run from backend/:
  python workers/scraper_pipeline.py
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
    print(f"SCRAPER PIPELINE — {start.strftime('%Y-%m-%d %H:%M UTC')}")
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

    run_step("Guardian",    Guardian)
    run_step("The Verge",   verge)
    run_step("Ars Technica", ars_technica)
    run_step("Axios",       axios)
    run_step("BBC",         bbc)
    run_step("Eater",       eater)
    run_step("ESPN",        espn)
    run_step("NPR",         npr)
    run_step("TechCrunch",  techcrunch)

    elapsed = (datetime.now(timezone.utc) - start).seconds
    print(f"\n{'=' * 55}")
    print(f"SCRAPER PIPELINE COMPLETE — {elapsed}s")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()
