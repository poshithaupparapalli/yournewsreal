"""
briefing_builder.py

Runs after summarizer.py.
For each user with a briefing today:
  1. Fetches their interest + learning articles + LLM summaries
  2. Formats a clean HTML briefing (same thing the email will send)
  3. Saves it to briefings.briefing_html so you can inspect it
  4. Prints a plain-text preview to the terminal

Run from backend/:
  python3 workers/ranking/briefing_builder.py
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

today = datetime.now(timezone.utc).date().isoformat()

DIVIDER = "─" * 60


def fetch_briefings() -> list[dict]:
    result = (
        supabase.table("briefings")
        .select("id, user_id, interest_article_ids, learning_article_ids")
        .eq("date", today)
        .execute()
    )
    return result.data


def fetch_users(user_ids: list[str]) -> dict[str, dict]:
    result = (
        supabase.table("users_waitlist")
        .select("id, name, email, interests_raw")
        .in_("id", user_ids)
        .execute()
    )
    return {u["id"]: u for u in result.data}


def fetch_articles(article_ids: list[str]) -> dict[str, dict]:
    if not article_ids:
        return {}
    result = (
        supabase.table("articles")
        .select("id, title, source, url, llm_summary")
        .in_("id", article_ids)
        .execute()
    )
    return {a["id"]: a for a in result.data}


def format_html_briefing(user: dict, interest_articles: list[dict], learning_articles: list[dict]) -> str:
    name = user.get("name") or user.get("email") or "there"
    first_name = name.split()[0]

    def article_block_html(article: dict, label: str = "") -> str:
        title   = article.get("title") or "Untitled"
        source  = (article.get("source") or "").replace("_", " ").title()
        url     = article.get("url") or "#"
        summary = article.get("llm_summary") or "<em>No summary available.</em>"
        tag     = f'<span style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px">{label}</span><br>' if label else ""
        return f"""
        <div style="margin-bottom:28px;padding-bottom:24px;border-bottom:1px solid #e8e8e8">
          {tag}
          <a href="{url}" style="font-size:18px;font-weight:600;color:#1a1a1a;text-decoration:none;line-height:1.3">
            {title}
          </a>
          <div style="font-size:12px;color:#999;margin:6px 0 10px">{source}</div>
          <p style="font-size:15px;color:#444;line-height:1.7;margin:0">{summary}</p>
        </div>
        """

    interest_blocks = "".join(article_block_html(a) for a in interest_articles)
    learning_blocks = "".join(article_block_html(a, label="learning pick") for a in learning_articles)

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:620px;margin:40px auto;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)">

    <!-- header -->
    <div style="background:#0d0d0d;padding:32px 40px">
      <div style="font-size:13px;color:#888;letter-spacing:2px;text-transform:uppercase">resonance</div>
      <div style="font-size:26px;font-weight:700;color:#ffffff;margin-top:6px">
        Good morning, {first_name}.
      </div>
      <div style="font-size:14px;color:#aaa;margin-top:4px">{today}</div>
    </div>

    <!-- articles -->
    <div style="padding:36px 40px">

      <div style="font-size:12px;color:#999;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:20px">
        Your briefing · {len(interest_articles)} stories + {len(learning_articles)} learning
      </div>

      {interest_blocks}

      {'<div style="margin:32px 0 24px"><div style="font-size:12px;color:#999;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:20px">Something new to learn</div>' + learning_blocks + '</div>' if learning_articles else ''}

    </div>

    <!-- footer -->
    <div style="padding:24px 40px;background:#f9f9f9;border-top:1px solid #eee">
      <p style="font-size:12px;color:#aaa;margin:0">
        You're getting this because you signed up for Resonance.<br>
        Curated for your interests — <em>{(user.get('interests_raw') or '')[:80]}...</em>
      </p>
    </div>

  </div>
</body>
</html>"""
    return html


def format_text_preview(user: dict, interest_articles: list[dict], learning_articles: list[dict]) -> str:
    name = user.get("name") or user.get("email") or "?"
    lines = [
        f"\n{DIVIDER}",
        f"  {name}  ({user.get('email', '')})",
        f"  Interests: {(user.get('interests_raw') or '')[:80]}...",
        DIVIDER,
    ]

    lines.append(f"\n  YOUR STORIES ({len(interest_articles)})\n")
    for a in interest_articles:
        title   = (a.get("title") or "Untitled")[:70]
        source  = (a.get("source") or "").replace("_", " ").title()
        summary = (a.get("llm_summary") or "No summary.")[:200]
        lines.append(f"  [{source}]")
        lines.append(f"  {title}")
        lines.append(f"  {summary}")
        lines.append("")

    if learning_articles:
        lines.append(f"  LEARNING PICK ({len(learning_articles)})\n")
        for a in learning_articles:
            title   = (a.get("title") or "Untitled")[:70]
            source  = (a.get("source") or "").replace("_", " ").title()
            summary = (a.get("llm_summary") or "No summary.")[:200]
            lines.append(f"  [{source}]")
            lines.append(f"  {title}")
            lines.append(f"  {summary}")
            lines.append("")

    return "\n".join(lines)


def save_briefing_html(briefing_id: str, html: str):
    supabase.table("briefings").update(
        {"briefing_html": html}
    ).eq("id", briefing_id).execute()


def run():
    print("\n" + "=" * 60)
    print("BRIEFING BUILDER")
    print("=" * 60 + "\n")

    briefings = fetch_briefings()
    if not briefings:
        print(f"No briefings found for {today}. Run ranker.py first.")
        return

    print(f"Found {len(briefings)} briefings for {today}\n")

    # collect all article IDs across all briefings to fetch in one query
    all_article_ids = []
    for b in briefings:
        all_article_ids += (b.get("interest_article_ids") or [])
        all_article_ids += (b.get("learning_article_ids") or [])
    all_article_ids = list(set(all_article_ids))

    user_ids = [b["user_id"] for b in briefings]

    users_map    = fetch_users(user_ids)
    articles_map = fetch_articles(all_article_ids)

    built  = 0
    failed = 0

    for briefing in briefings:
        user_id = briefing["user_id"]
        user    = users_map.get(user_id, {"name": "Unknown", "email": user_id})

        interest_ids = briefing.get("interest_article_ids") or []
        learning_ids = briefing.get("learning_article_ids") or []

        # preserve the ranker's ordering
        interest_articles = [articles_map[aid] for aid in interest_ids if aid in articles_map]
        learning_articles = [articles_map[aid] for aid in learning_ids if aid in articles_map]

        # warn if summaries are missing
        missing = [a["id"] for a in interest_articles + learning_articles if not a.get("llm_summary")]
        if missing:
            print(f"  ⚠ {len(missing)} article(s) missing summaries — run summarizer.py first")

        try:
            html = format_html_briefing(user, interest_articles, learning_articles)
            save_briefing_html(briefing["id"], html)

            print(format_text_preview(user, interest_articles, learning_articles))
            built += 1
        except Exception as e:
            name = user.get("name") or user_id[:8]
            print(f"  ✗ Failed for {name}: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"DONE — {built} briefings built, {failed} failed")
    print(f"HTML saved to briefings.briefing_html in Supabase")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    run()
