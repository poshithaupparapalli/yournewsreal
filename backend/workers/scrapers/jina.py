import os
import sys
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
JINA_API_KEY        = os.getenv("JINA_API_KEY")  # optional — remove header if not using
BODY_PREVIEW_CHARS  = 1500
DELAY_BETWEEN_REQS  = 1.5  # seconds — be polite to Jina
# ─────────────────────────────────────────────────────────────


def fetch_unfetched_links() -> list[dict]:
    """
    Pulls all rows from article_links where fetched = False.
    """
    try:
        result = supabase.table("article_links").select("*").eq("fetched", False).execute()
        return result.data or []
    except Exception as e:
        print(f"  ⚠ Failed to fetch unfetched links: {e}")
        return []


def fetch_full_article(url: str) -> str | None:
    """
    Sends a URL through Jina Reader (r.jina.ai) and returns
    the full article text, or None if it fails.
    """
    jina_url = f"https://r.jina.ai/{url}"

    headers = {"Accept": "text/plain"}
    if JINA_API_KEY:
        headers["Authorization"] = f"Bearer {JINA_API_KEY}"

    try:
        response = requests.get(jina_url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"  ⚠ Jina returned {response.status_code} for {url[:60]}")
            return None
    except Exception as e:
        print(f"  ⚠ Jina request failed for {url[:60]}: {e}")
        return None


def save_article(link: dict, body_text: str) -> bool:
    """
    Inserts a fully fetched article into the articles table
    and marks the source link as fetched.
    """
    body_preview = body_text[:BODY_PREVIEW_CHARS] if body_text else None

    article = {
        "guardian_id":  link.get("url"),           # N/A — not a Guardian article
        "title":        link.get("title"),
        "url":          link.get("url"),
        "published_at": link.get("published_at"),
        "section":      None,           # RSS feeds don't provide section
        "author":       None,           # RSS feeds don't reliably provide author
        "summary":      body_preview,   # first 1500 chars of full article
        "body_text":    body_text,
        "source":       link.get("source"),
        "scraped_at":   datetime.now(timezone.utc).isoformat(),
        "body_preview": body_preview,
        "embedding":    None,           # to be added later
    }

    try:
        # Insert article
        supabase.table("articles").upsert(article, on_conflict="url", ignore_duplicates=True).execute()

        # Mark as fetched in article_links
        supabase.table("article_links").update({"fetched": True}).eq("id", link["id"]).execute()

        return True
    except Exception as e:
        print(f"  ⚠ Failed to save article for {link.get('url', '')[:60]}: {e}")
        return False


def run():
    print(f"\n{'=' * 55}")
    print(f"JINA FETCHER")
    print(f"{'=' * 55}")

    links = fetch_unfetched_links()

    if not links:
        print("\nNo unfetched articles found. Exiting.")
        return

    print(f"\nFound {len(links)} unfetched articles")
    print(f"Fetching full text via Jina...\n")

    saved   = 0
    skipped = 0

    for i, link in enumerate(links, 1):
        url = link.get("url", "")
        print(f"  [{i}/{len(links)}] {url[:70]}")

        body_text = fetch_full_article(url)

        if not body_text:
            print(f"         ↳ No content returned, skipping")
            skipped += 1
            continue

        success = save_article(link, body_text)

        if success:
            print(f"         ↳ Saved ({len(body_text):,} chars)")
            saved += 1
        else:
            skipped += 1

        time.sleep(DELAY_BETWEEN_REQS)

    print(f"\n{'=' * 55}")
    print(f"DONE — {saved} articles saved, {skipped} skipped")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()