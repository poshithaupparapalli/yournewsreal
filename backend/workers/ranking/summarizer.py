"""
summarizer.py

Runs after ranker.py and before emailer.py.
Reads all of today's briefings, collects the unique articles needed,
and generates a 3-5 sentence LLM summary for each one.

Summaries are stored in articles.llm_summary and reused across all
users who received the same article — so each article is only
summarized once regardless of how many users get it.

Run from backend/:
  python workers/ranking/summarizer.py
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────────────────────
# CONFIG
MODEL        = "gpt-4o-mini"   # fast and cheap — good enough for summarization
MAX_TOKENS   = 180             # ~3-5 sentences
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a concise news summarizer. Given a news article, write a 3-5 sentence summary that:
- Captures the key facts and why this story matters
- Is written in plain, clear language
- Does not start with "This article" or "The article"
- Does not include any opinion or editorializing
- Reads naturally as a standalone paragraph

Return only the summary, nothing else."""


def get_todays_briefings() -> list[dict]:
    """
    Fetches all briefings created today.
    Returns a list of briefing rows each with an article_ids array.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    result = (
        supabase.table("briefings")
        .select("interest_article_ids, learning_article_ids, world_article_ids")
        .eq("date", today)
        .execute()
    )
    return result.data


def get_unique_article_ids(briefings: list[dict]) -> list[str]:
    """
    Flattens all article_ids across all briefings into a deduplicated list.
    This ensures we only summarize each article once even if it appears
    in multiple users' briefings.
    """
    seen = set()
    unique_ids = []
    for briefing in briefings:
        all_ids = (
            (briefing.get("interest_article_ids") or []) +
            (briefing.get("learning_article_ids") or []) +
            (briefing.get("world_article_ids") or [])
        )
        for article_id in all_ids:
            if article_id not in seen:
                seen.add(article_id)
                unique_ids.append(article_id)
    return unique_ids


def fetch_articles_needing_summary(article_ids: list[str]) -> list[dict]:
    """
    Fetches articles that are in today's briefings but don't have
    an llm_summary yet. Skips already-summarized articles so this
    is safe to re-run without wasting API calls.
    """
    result = (
        supabase.table("articles")
        .select("id, title, body_text")
        .in_("id", article_ids)
        .is_("llm_summary", "null")
        .execute()
    )
    return result.data


def summarize_article(title: str, body_text: str) -> str | None:
    """
    Calls GPT-4o-mini to generate a 3-5 sentence summary of the article.
    Returns the summary string, or None if the call fails.
    """
    # Truncate body to first 3000 chars — enough context for a good summary
    # and keeps token costs low
    truncated_body = body_text[:3000] if body_text else ""

    if not truncated_body:
        return None

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Title: {title}\n\n{truncated_body}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"    ✗ OpenAI error: {e}")
        return None


def save_summary(article_id: str, summary: str):
    """
    Saves the generated summary back to the articles table.
    """
    supabase.table("articles").update(
        {"llm_summary": summary}
    ).eq("id", article_id).execute()


def run():
    print("\n" + "=" * 55)
    print("SUMMARIZER")
    print("=" * 55 + "\n")

    # Step 1 — find all articles needed for today's briefings
    briefings = get_todays_briefings()
    if not briefings:
        print("No briefings found for today. Run ranker.py first.")
        return

    print(f"Found {len(briefings)} briefings for today")

    unique_ids = get_unique_article_ids(briefings)
    print(f"Unique articles across all briefings: {len(unique_ids)}")

    # Step 2 — filter to only ones missing a summary
    articles = fetch_articles_needing_summary(unique_ids)
    if not articles:
        print("All articles already have summaries. Exiting.")
        return

    print(f"Articles needing summaries: {len(articles)}\n")

    summarized = 0
    failed     = 0

    # Step 3 — summarize each one
    for i, article in enumerate(articles, 1):
        title     = article.get("title", "")
        body_text = article.get("body_text", "")

        print(f"  [{i}/{len(articles)}] {title[:65]}")

        summary = summarize_article(title, body_text)

        if summary is None:
            print(f"    ✗ Failed to summarize")
            failed += 1
            continue

        save_summary(article["id"], summary)
        summarized += 1
        print(f"    ✓ {len(summary)} chars")

    print(f"\n{'=' * 55}")
    print(f"DONE")
    print(f"  Summarized: {summarized}")
    print(f"  Failed:     {failed}")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()