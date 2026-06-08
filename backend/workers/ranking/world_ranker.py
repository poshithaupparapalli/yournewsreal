"""
world_ranker.py

Runs after ranker.py.
1. Reads today's world_candidates from Supabase
2. Sends titles + summaries to GPT-4o-mini to rank by global significance
3. Stores llm_rank back on each candidate
4. For each user, assigns top 3 world articles whose cluster_id
   doesn't already appear in their interest or learning briefing slots

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

WORLD_SLOTS = 1


def fetch_todays_candidates() -> list[dict]:
    """
    Fetches today's world candidates joined with their cluster_id
    from the articles table.
    """
    today = datetime.now(timezone.utc).date().isoformat()

    result = (
        supabase.table("world_candidates")
        .select("id, guardian_id, title, summary, date")
        .eq("date", today)
        .execute()
    )

    candidates = result.data
    if not candidates:
        return []

    # Enrich each candidate with cluster_id and article uuid from articles table
    enriched = []
    for c in candidates:
        article = supabase.table("articles").select(
            "id, cluster_id"
        ).eq("guardian_id", c["guardian_id"]).execute()

        if article.data:
            c["article_id"]  = article.data[0]["id"]
            c["cluster_id"]  = article.data[0]["cluster_id"]
        else:
            c["article_id"]  = None
            c["cluster_id"]  = None

        enriched.append(c)

    return enriched


def rank_with_llm(candidates: list[dict]) -> list[str]:
    """
    Sends candidate titles and summaries to GPT-4o-mini.
    Returns a list of guardian_ids ordered by global significance.
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
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    raw = raw.strip()

    # If response was truncated, try to recover a partial list
    if not raw.endswith("]"):
        last_quote = raw.rfind('"')
        if last_quote > 0:
            raw = raw[:last_quote + 1] + "]"

    return json.loads(raw)


def save_llm_ranks(ranked_ids: list[str]):
    """
    Writes llm_rank back to each world_candidate row.
    Rank 1 = most significant.
    """
    for rank, guardian_id in enumerate(ranked_ids, 1):
        supabase.table("world_candidates").update(
            {"llm_rank": rank}
        ).eq("guardian_id", guardian_id).execute()


def get_existing_cluster_ids(article_ids: list[str]) -> set[int]:
    """
    Given a list of article UUIDs already in a user's briefing,
    returns the set of cluster_ids they belong to.
    """
    if not article_ids:
        return set()

    result = (
        supabase.table("articles")
        .select("cluster_id")
        .in_("id", article_ids)
        .execute()
    )

    return {
        row["cluster_id"]
        for row in result.data
        if row["cluster_id"] is not None
    }


def fetch_todays_briefings() -> list[dict]:
    """
    Fetches all briefings created today.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    result = (
        supabase.table("briefings")
        .select("id, user_id, interest_article_ids, learning_article_ids")
        .eq("date", today)
        .execute()
    )
    return result.data


def assign_world_articles(briefings: list[dict], ranked_candidates: list[dict]) -> int:
    """
    For each user briefing, walks down the ranked world candidates
    and assigns the top 3 whose cluster_id doesn't already appear
    in the user's interest or learning picks.
    """
    updated = 0

    for briefing in briefings:
        briefing_id = briefing["id"]

        # Get all article IDs already in this briefing
        existing_article_ids = (
            (briefing.get("interest_article_ids") or []) +
            (briefing.get("learning_article_ids") or [])
        )

        # Look up which clusters are already represented
        existing_cluster_ids = get_existing_cluster_ids(existing_article_ids)

        world_ids = []

        for candidate in ranked_candidates:
            if len(world_ids) >= WORLD_SLOTS:
                break

            article_id = candidate.get("article_id")
            cluster_id = candidate.get("cluster_id")

            # Skip if article not found in articles table
            if not article_id:
                continue

            # Skip if this cluster is already represented in the briefing
            if cluster_id is not None and cluster_id in existing_cluster_ids:
                print(f"    Skipping cluster {cluster_id} — already in briefing")
                continue

            world_ids.append(article_id)
            existing_cluster_ids.add(cluster_id)

        # Save world article IDs to briefing
        supabase.table("briefings").update(
            {"world_article_ids": world_ids}
        ).eq("id", briefing_id).execute()

        print(f"  ✓ User {briefing['user_id'][:8]}... → {len(world_ids)} world articles")
        updated += 1

    return updated


def run():
    print("\n" + "=" * 55)
    print("WORLD RANKER")
    print("=" * 55 + "\n")

    # Step 1 — fetch today's world candidates with cluster IDs
    candidates = fetch_todays_candidates()
    if not candidates:
        print("No world candidates found for today.")
        print("Run guardian_world_scraper.py first.")
        return

    print(f"Found {len(candidates)} world candidates")
    missing = sum(1 for c in candidates if not c.get("article_id"))
    if missing:
        print(f"  ⚠ {missing} candidates not found in articles table — will be skipped")

    # Step 2 — rank with LLM
    print("\nRanking with GPT-4o-mini...")
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

    # Step 5 — fetch briefings and assign world articles
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

def run_for_user(user_id: str):
    """
    On-demand version of run() for new users signing up mid-day.
    Reuses already-ranked world candidates (no LLM re-call needed)
    and assigns world articles to just this user's briefing.
    """
    print("\n" + "=" * 55)
    print(f"WORLD RANKER — on-demand for user {user_id[:8]}...")
    print("=" * 55 + "\n")

    # Fetch already-ranked candidates for today (ranked by daily pipeline or previous on-demand run)
    today = datetime.now(timezone.utc).date().isoformat()
    result = (
        supabase.table("world_candidates")
        .select("id, guardian_id, title, summary, date, llm_rank")
        .eq("date", today)
        .order("llm_rank", desc=False)
        .execute()
    )
    candidates = result.data

    if not candidates:
        print("No world candidates found for today — skipping world articles.")
        return

    # Enrich with article_id and cluster_id
    enriched = []
    for c in candidates:
        article = supabase.table("articles").select(
            "id, cluster_id"
        ).eq("guardian_id", c["guardian_id"]).execute()

        if article.data:
            c["article_id"] = article.data[0]["id"]
            c["cluster_id"] = article.data[0]["cluster_id"]
        else:
            c["article_id"] = None
            c["cluster_id"] = None

        enriched.append(c)

    # If candidates haven't been LLM-ranked yet (llm_rank is null), rank now
    unranked = [c for c in enriched if c.get("llm_rank") is None]
    if unranked:
        print("Candidates not yet ranked — running LLM ranking now...")
        ranked_ids = rank_with_llm(enriched)
        save_llm_ranks(ranked_ids)
        id_to_candidate = {c["guardian_id"]: c for c in enriched}
        ranked_candidates = [
            id_to_candidate[gid] for gid in ranked_ids
            if gid in id_to_candidate
        ]
    else:
        ranked_candidates = sorted(enriched, key=lambda c: c.get("llm_rank") or 999)

    # Fetch just this user's briefing
    briefing_result = (
        supabase.table("briefings")
        .select("id, user_id, interest_article_ids, learning_article_ids")
        .eq("user_id", user_id)
        .eq("date", today)
        .execute()
    )

    if not briefing_result.data:
        print(f"No briefing found for user {user_id[:8]}... — skipping.")
        return

    updated = assign_world_articles(briefing_result.data, ranked_candidates)
    print(f"\n{'=' * 55}")
    print(f"DONE — updated {updated} briefing")
    print(f"{'=' * 55}\n")