"""
world_ranker.py

Runs after ranker.py.
1. Reads today's world_candidates from Supabase
2. Sends titles + summaries to GPT-4o-mini to rank by global significance
3. Stores llm_rank back on each candidate
4. For each user, assigns top 3 world articles that aren't already
   in their interest or learning briefing slots

Run from backend/:
  python workers/ranking/world_ranker.py
"""

import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WORLD_SLOTS = 3


def fetch_todays_candidates() -> list[dict]:
    """
    Fetches today's world candidates from Supabase.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    result = (
        supabase.table("world_candidates")
        .select("id, guardian_id, title, summary")
        .eq("date", today)
        .execute()
    )
    return result.data


def rank_with_llm(candidates: list[dict]) -> list[str]:
    """
    Sends candidate titles and summaries to GPT-4o-mini.
    Returns a list of guardian_ids ordered by global significance (most → least).
    """
    articles_text = "\n\n".join([
        f"ID: {c['guardian_id']}\nTitle: {c['title']}\nSummary: {c.get('summary', '')}"
        for c in candidates
    ])

    prompt = f"""You are an editor selecting the most globally significant news stories of the day.

Below are {len(candidates)} articles from Guardian's world section. Rank them from most to least globally significant — prioritize stories with major geopolitical impact, large scale of people affected, historical significance, or major economic consequences. Deprioritize regional stories with limited global impact.

Return ONLY a JSON array of the article IDs in order from most to least significant. No explanation.

Articles:
{articles_text}

Return format: ["id1", "id2", "id3", ...]"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    ranked_ids = json.loads(raw.strip())
    return ranked_ids


def save_llm_ranks(ranked_ids: list[str]):
    """
    Writes llm_rank back to each world_candidate row.
    Rank 1 = most significant.
    """
    for rank, guardian_id in enumerate(ranked_ids, 1):
        supabase.table("world_candidates").update(
            {"llm_rank": rank}
        ).eq("guardian_id", guardian_id).execute()


def fetch_todays_briefings() -> list[dict]:
    """
    Fetches all briefings created today so we can check
    which articles are already assigned to each user.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    result = (
        supabase.table("briefings")
        .select("id, user_id, interest_article_ids, learning_article_ids")
        .eq("date", today)
        .execute()
    )
    return result.data


def get_article_id_for_guardian_id(guardian_id: str) -> str | None:
    """
    Looks up the articles table to get the uuid for a guardian_id.
    World candidates use guardian_id but briefings store uuid.
    """
    result = (
        supabase.table("articles")
        .select("id")
        .eq("guardian_id", guardian_id)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]
    return None


def assign_world_articles(briefings: list[dict], ranked_candidates: list[dict]):
    """
    For each user briefing, walks down the ranked world candidates
    and assigns the top 3 that aren't already in their briefing.
    """
    updated = 0

    for briefing in briefings:
        briefing_id = briefing["id"]
        existing_ids = set(
            (briefing.get("interest_article_ids") or []) +
            (briefing.get("learning_article_ids") or [])
        )

        world_ids = []

        for candidate in ranked_candidates:
            if len(world_ids) >= WORLD_SLOTS:
                break

            # Get the uuid for this guardian_id
            article_id = get_article_id_for_guardian_id(candidate["guardian_id"])

            if not article_id:
                continue  # article not in our articles table yet

            if article_id in existing_ids:
                continue  # already in this user's briefing

            world_ids.append(article_id)
            existing_ids.add(article_id)

        # Save world article IDs to briefing
        supabase.table("briefings").update(
            {"world_article_ids": world_ids}
        ).eq("id", briefing_id).execute()

        updated += 1

    return updated


def run():
    print("\n" + "=" * 55)
    print("WORLD RANKER")
    print("=" * 55 + "\n")

    # Step 1 — fetch today's world candidates
    candidates = fetch_todays_candidates()
    if not candidates:
        print("No world candidates found for today. Run guardian_world_scraper.py first.")
        return

    print(f"Found {len(candidates)} world candidates\n")

    # Step 2 — rank with LLM
    print("Ranking with GPT-4o-mini...")
    ranked_ids = rank_with_llm(candidates)
    print(f"  Ranked {len(ranked_ids)} articles")

    # Step 3 — save ranks back to Supabase
    save_llm_ranks(ranked_ids)

    # Step 4 — sort candidates by llm_rank
    id_to_candidate = {c["guardian_id"]: c for c in candidates}
    ranked_candidates = [
        id_to_candidate[gid] for gid in ranked_ids
        if gid in id_to_candidate
    ]

    # Step 5 — assign to each user's briefing
    print("\nAssigning world articles to briefings...")
    briefings = fetch_todays_briefings()

    if not briefings:
        print("No briefings found for today. Run ranker.py first.")
        return

    updated = assign_world_articles(briefings, ranked_candidates)

    print(f"\n{'=' * 55}")
    print(f"DONE — updated {updated} briefings")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()