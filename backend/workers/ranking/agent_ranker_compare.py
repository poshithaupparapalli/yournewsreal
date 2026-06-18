"""
claude_ranker_compare.py

Compares cosine similarity picks vs Claude's picks for every user.
Does NOT modify any data — read only except for Claude API calls.

Run from backend/:
  python workers/ranking/claude_ranker_compare.py
"""

import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import anthropic

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL      = "claude-sonnet-4-6"
MAX_TOKENS = 512


def fetch_todays_briefings() -> list[dict]:
    today = datetime.now(timezone.utc).date().isoformat()
    result = (
        supabase.table("briefings")
        .select("user_id, interest_article_ids, learning_article_ids")
        .eq("date", today)
        .execute()
    )
    return result.data or []


def fetch_users(user_ids: list[str]) -> dict[str, dict]:
    result = (
        supabase.table("users")
        .select("id, interests_raw, learning_goals_raw")
        .in_("id", user_ids)
        .execute()
    )
    return {u["id"]: u for u in (result.data or [])}


def fetch_articles() -> list[dict]:
    result = (
        supabase.table("articles")
        .select("id, title, source")
        .not_.is_("embedding", "null")
        .execute()
    )
    return result.data or []


def fetch_article_titles(article_ids: list[str], article_map: dict) -> list[str]:
    return [
        article_map[aid]["title"]
        for aid in article_ids
        if aid in article_map
    ]


def ask_claude(interests: str, learning: str, articles: list[dict]) -> list[str]:
    """
    Sends the user profile + article list to Claude.
    Returns a list of up to 5 article IDs Claude chose.
    """
    # Format articles as a numbered list of "ID: title (source)"
    # We use the index number in the prompt but pass the real ID so Claude returns it
    article_lines = "\n".join(
        f"{i+1}. [{a['id']}] {a['title']} ({a.get('source', '')})"
        for i, a in enumerate(articles)
    )

    prompt = f"""You are picking a personalized news briefing for a user.

User interests: {interests}
User learning goals: {learning}

Here are today's available articles (format: [article_id] title (source)):

{article_lines}

Pick exactly 5 article IDs that best match this user's interests and learning goals.
Return ONLY a JSON array of 5 article ID strings, nothing else.
Example: ["id1", "id2", "id3", "id4", "id5"]"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        import re
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if not match:
            return []
        ids = json.loads(match.group()) 
        # Validate — only return IDs that actually exist in our article list
        valid_ids = {a["id"] for a in articles}
        return [aid for aid in ids if aid in valid_ids][:5]
    except Exception as e:
        print(f"    Claude error: {e}")
        return []


def run():
    print("\n" + "=" * 60)
    print("CLAUDE vs COSINE — COMPARISON REPORT")
    print("=" * 60)

    briefings = fetch_todays_briefings()
    if not briefings:
        print("No briefings found for today. Run the pipeline first.")
        return

    user_ids = [b["user_id"] for b in briefings]
    users    = fetch_users(user_ids)
    articles = fetch_articles()

    # Build a lookup map: article_id → article dict
    article_map = {a["id"]: a for a in articles}

    print(f"Users with briefings today: {len(briefings)}")
    print(f"Articles in pool:           {len(articles)}")
    print(f"Model:                      {MODEL}\n")

    for i, briefing in enumerate(briefings, 1):
        user_id = briefing["user_id"]
        user    = users.get(user_id)

        if not user:
            continue

        interests = user.get("interests_raw") or "(none)"
        learning  = user.get("learning_goals_raw") or "(none)"

        # Cosine picks — already in the briefing
        cosine_ids = (
            (briefing.get("interest_article_ids") or []) +
            (briefing.get("learning_article_ids") or [])
        )
        cosine_titles = fetch_article_titles(cosine_ids, article_map)

        print(f"\n{'═' * 60}")
        print(f"USER {i}/{len(briefings)}: {user_id[:8]}...")
        print(f"Interests:  {interests[:100]}")
        print(f"Learning:   {learning[:100]}")
        print()

        print("COSINE PICKS:")
        for j, title in enumerate(cosine_titles, 1):
            print(f"  {j}. {title[:80]}")

        # Claude picks
        print("\nAsking Claude...")
        claude_ids    = ask_claude(interests, learning, articles)
        claude_titles = fetch_article_titles(claude_ids, article_map)

        print("\nCLAUDE PICKS:")
        for j, title in enumerate(claude_titles, 1):
            print(f"  {j}. {title[:80]}")

        # Overlap — how many picks do they share?
        overlap = set(cosine_ids) & set(claude_ids)
        print(f"\nOverlap: {len(overlap)}/5 articles in common")

    print(f"\n{'=' * 60}")
    print("DONE")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    run()