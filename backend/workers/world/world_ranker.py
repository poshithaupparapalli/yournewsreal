"""
world_ranker.py

Runs after ranker.py, before summarizer.py.
1. Fetches top world headlines from NewsAPI (title + description, no scraping needed)
2. GPT scores each for global significance
3. Filters out stories already covered in the last 7 days (story repetition check)
4. Takes the top scorer >= 6 that hasn't been seen recently
5. Tries to Jina-scrape the winner for full body text (for the summary)
   If scrape fails, uses the NewsAPI description as fallback
6. Inserts into articles table, updates all today's briefings

Run from backend/:
  python3 workers/world/world_ranker.py
"""

import requests, os, sys
import numpy as np
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

client       = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
NEWSAPI_KEY  = os.getenv("NEWSAPI_KEY", "")
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_HEADERS = {"Authorization": f"Bearer {JINA_API_KEY}"} if JINA_API_KEY else {}

MIN_GPT_SCORE     = 6.0
EMBEDDING_MODEL   = "text-embedding-3-small"

# Per-user dedup threshold: if the world article is this similar to something
# already in a user's briefing (interest/learning), skip the world slot for them.
# Set higher (0.82) because we only want to skip when it's essentially the same article.
SIMILARITY_CUTOFF = 0.82

# Story repeat threshold: if today's candidate is this similar to any world article
# we've already run in the last 7 days, skip it and try the next candidate.
# Set lower (0.78) than SIMILARITY_CUTOFF so we catch "same ongoing story, new angle"
# e.g. "Russia attacks Kyiv" today vs "Russia threatens Kyiv strikes" yesterday.
STORY_REPEAT_CUTOFF = 0.78

# How many days back to look when checking for story repetition.
# 7 days means a major ongoing story (war, crisis) needs to have gone quiet
# for a full week before we'll surface it again as the world pick.
STORY_REPEAT_WINDOW_DAYS = 7

# NewsAPI sources — major trusted outlets only
NEWSAPI_SOURCES = ",".join([
    "reuters", "associated-press", "bbc-news", "cnn", "nbc-news",
    "abc-news", "cbs-news", "the-washington-post", "bloomberg",
    "politico", "axios", "npr", "foreign-policy", "the-hill",
    "newsweek", "time", "business-insider", "fox-news",
])

SIGNIFICANCE_PROMPT = """You are a world news editor scoring articles for global significance.

Score this article 0-10 on how much the world needs to know about it today.

Scoring guide:
  9-10 = War, pandemic, global economic crisis, world leader death
  7-8  = Major geopolitical event, significant policy change affecting many countries
  5-6  = Important national event with international implications
  3-4  = Significant but mostly local or single-country impact
  1-2  = Entertainment, celebrity, sports, local crime, minor incidents
  0    = Irrelevant, PR content, purely local

Hard rules:
- Celebrity/royal family news → max score 2
- Sports → max score 2
- Local accidents/crime → max score 3
- Anything affecting only one city → max score 3

Return ONLY this exact format, nothing else:
SCORE: [number 0-10]
REASON: [one sentence why]
CATEGORY: [one of: geopolitics / conflict / economy / science / health / climate / domestic-politics / celebrity / sports / local]"""


# ── NewsAPI ───────────────────────────────────────────────────────────────────

def fetch_newsapi_headlines(page_size: int = 30) -> list[dict]:
    """
    Fetches top world headlines from NewsAPI.
    Returns list of articles with title, description, source, url.
    """
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "sources":  NEWSAPI_SOURCES,
        "pageSize": page_size,
        "apiKey":   NEWSAPI_KEY,
    }
    r = requests.get(url, params=params, timeout=15)
    data = r.json()

    if data.get("status") != "ok":
        print(f"  ✗ NewsAPI error: {data.get('message')}")
        return []

    articles = []
    for a in data.get("articles", []):
        title       = (a.get("title") or "").strip()
        description = (a.get("description") or "").strip()
        source      = (a.get("source", {}).get("name") or "").strip()
        url         = (a.get("url") or "").strip()

        if not title or not url:
            continue
        # skip removed articles
        if title == "[Removed]":
            continue

        articles.append({
            "title":       title,
            "description": description,
            "source":      source,
            "url":         url,
        })

    return articles


# ── GPT scoring ───────────────────────────────────────────────────────────────

def score_significance(title: str, description: str) -> tuple[float | None, str, str]:
    content = f"Title: {title}\n\nDescription: {description}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=80,
            messages=[
                {"role": "system", "content": SIGNIFICANCE_PROMPT},
                {"role": "user",   "content": content},
            ]
        )
        text = resp.choices[0].message.content.strip()

        score    = None
        reason   = ""
        category = ""
        for line in text.splitlines():
            if line.startswith("SCORE:"):
                try: score = float(line.replace("SCORE:", "").strip())
                except: pass
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
            elif line.startswith("CATEGORY:"):
                category = line.replace("CATEGORY:", "").strip()

        return score, reason, category
    except Exception as e:
        return None, str(e), ""


# ── Jina scrape (best effort for full body) ───────────────────────────────────

def scrape_jina(url: str) -> str | None:
    """
    Tries to get full article body via Jina.
    Returns body text or None if blocked.
    """
    try:
        r = requests.get(f"https://r.jina.ai/{url}", headers=JINA_HEADERS, timeout=20)
        text = r.text.strip()

        blocked = r.status_code in [451, 403] or any(x in text.lower() for x in [
            "securitycompromiseerror", "authenticationfailed", "paywall",
            "subscribe to read", "are you a robot", "captcha",
        ])
        if blocked or len(text) < 500:
            return None

        body_lines = []
        in_body = False
        for line in text.splitlines():
            if line.startswith("Markdown Content:"):
                in_body = True
                continue
            if in_body and line.strip():
                body_lines.append(line.strip())
            if len(" ".join(body_lines)) > 3000:
                break

        body = " ".join(body_lines)[:3000]
        return body if len(body) > 300 else None
    except:
        return None


# ── Embedding + similarity ────────────────────────────────────────────────────

def embed_text(text: str) -> np.ndarray | None:
    try:
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=text[:8000])
        return np.array(resp.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(f"  ✗ Embedding failed: {e}")
        return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def parse_embedding(v) -> np.ndarray:
    """
    Supabase returns pgvector embeddings as a JSON string like '[-0.03, 0.06, ...]'
    rather than a Python list. This handles both formats safely.
    """
    import json
    if isinstance(v, str):
        return np.array(json.loads(v), dtype=np.float32)
    return np.array(v, dtype=np.float32)


# ── Story repeat check ────────────────────────────────────────────────────────

def fetch_recent_world_articles(days: int = STORY_REPEAT_WINDOW_DAYS) -> list[dict]:
    """
    Fetches world articles we've already run in the last N days.

    We identify world articles by their source field — world_ranker.py always
    saves them with source = "newsapi_world_<category>" (e.g. "newsapi_world_conflict").
    This is how we distinguish them from regular scraped articles.

    We pull their embeddings so we can do cosine similarity against today's candidates.
    If a candidate is too similar to one of these past articles, we skip it —
    this prevents the same ongoing story (e.g. Russia/Ukraine) from dominating
    the world slot every single day.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    result = (
        supabase.table("articles")
        .select("title, embedding")
        # Only world articles — identified by the source prefix we set on insert
        .like("source", "newsapi_world_%")
        # Only articles from the last N days
        .gte("published_at", cutoff)
        # Only ones that have embeddings (we always embed world articles, but just in case)
        .not_.is_("embedding", "null")
        .execute()
    )
    return result.data or []


def is_repeat_story(
    candidate_title: str,
    candidate_description: str,
    recent_world_articles: list[dict],
) -> tuple[bool, str, float]:
    """
    Checks whether a candidate article is essentially the same story as one
    we've already run in the last 7 days.

    How it works:
      1. Embed the candidate (title + description combined for richer signal)
      2. Compare against each recent world article's embedding via cosine similarity
      3. If any similarity >= STORY_REPEAT_CUTOFF (0.78), it's a repeat

    Why title + description?
      Using just the title might miss same-story matches with different headlines
      ("Russia attacks Kyiv" vs "Ukraine repels overnight assault"). The description
      adds enough context to catch these topic-level matches.

    Returns:
      (is_repeat, matched_title, similarity_score)
      If not a repeat, matched_title="" and similarity_score=0.0
    """
    if not recent_world_articles:
        # No past world articles → nothing to compare against → not a repeat
        return False, "", 0.0

    candidate_emb = embed_text(f"{candidate_title} {candidate_description}")
    if candidate_emb is None:
        # Embedding failed — don't block the candidate, just let it through
        return False, "", 0.0

    for past in recent_world_articles:
        if not past.get("embedding"):
            continue
        past_emb = parse_embedding(past["embedding"])
        sim = cosine_similarity(candidate_emb, past_emb)
        if sim >= STORY_REPEAT_CUTOFF:
            return True, past["title"], sim

    return False, "", 0.0


# ── Supabase ──────────────────────────────────────────────────────────────────

def insert_world_article(title: str, url: str, body_text: str, source: str, category: str, embedding: np.ndarray | None) -> str | None:
    payload = {
        "title":        title,
        "url":          url,
        "source":       f"newsapi_world_{category}",
        "body_text":    body_text,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "guardian_id":  url,
    }
    if embedding is not None:
        payload["embedding"] = embedding.tolist()

    result = supabase.table("articles").upsert(payload, on_conflict="guardian_id").execute()
    if result.data:
        return result.data[0]["id"]

    fetch = supabase.table("articles").select("id").eq("guardian_id", url).single().execute()
    return fetch.data["id"] if fetch.data else None


def update_briefings_world_per_user(article_id: str, world_embedding: np.ndarray | None):
    """
    Adds the world article to each user's briefing for today.

    Per-user dedup: if the world article is too similar (>= 0.82) to something
    the user already has in their interest or learning slots, we skip their world
    slot entirely. This prevents a user from getting the same story twice — once
    as a personal interest pick and again as the global world pick.

    Note: this is different from the story repeat check above. The repeat check
    happens once globally before picking the winner. This check happens per user
    after we've already decided the winner.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    briefings = (
        supabase.table("briefings")
        .select("id, user_id, interest_article_ids, learning_article_ids")
        .eq("date", today)
        .execute()
        .data
    )

    added = 0
    skipped = 0

    for b in briefings:
        existing_ids = (b.get("interest_article_ids") or []) + (b.get("learning_article_ids") or [])
        too_similar = False

        if world_embedding is not None and existing_ids:
            existing = (
                supabase.table("articles")
                .select("id, embedding")
                .in_("id", existing_ids)
                .not_.is_("embedding", "null")
                .execute()
                .data
            )
            for art in existing:
                if not art.get("embedding"):
                    continue
                emb = parse_embedding(art["embedding"])
                sim = cosine_similarity(world_embedding, emb)
                if sim >= SIMILARITY_CUTOFF:
                    too_similar = True
                    print(f"  ⚠ Skipping world for user {b['user_id'][:8]}... (similarity {sim:.2f})")
                    break

        if too_similar:
            skipped += 1
            continue

        supabase.table("briefings").update(
            {"world_article_ids": [article_id]}
        ).eq("id", b["id"]).execute()
        added += 1

    print(f"  ✓ Added to {added} briefings, skipped {skipped} (already covered)")


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("\n" + "=" * 55)
    print("WORLD RANKER")
    print("=" * 55 + "\n")

    # ── Step 1: fetch headlines from NewsAPI ──────────────────
    print("  Fetching headlines from NewsAPI...")
    articles = fetch_newsapi_headlines(page_size=30)
    if not articles:
        print("  ✗ No articles from NewsAPI. Exiting.")
        return

    print(f"  Got {len(articles)} headlines\n")
    print(f"  {'─'*55}")
    print(f"  RAW NEWSAPI HEADLINES")
    print(f"  {'─'*55}")
    for i, a in enumerate(articles, 1):
        print(f"  #{i:2} [{a['source']}]")
        print(f"       {a['title'][:80]}")
        print(f"       {a['description'][:100] if a['description'] else 'no description'}")
        print()

    # ── Step 2: GPT score each ────────────────────────────────
    print(f"\n  {'─'*55}")
    print(f"  GPT SCORING")
    print(f"  {'─'*55}\n")

    scored = []
    for i, a in enumerate(articles, 1):
        score, reason, category = score_significance(a["title"], a["description"])
        if score is None:
            print(f"  [{i:2}] GPT failed — {a['title'][:50]}")
            continue
        icon = "✅" if score >= 7 else "🟡" if score >= 5 else "❌"
        print(f"  [{i:2}] {icon} {score}/10 [{category}] [{a['source']}]")
        print(f"        {a['title'][:70]}")
        print(f"        {reason[:80]}")
        print()
        scored.append({**a, "score": score, "reason": reason, "category": category})

    scored.sort(key=lambda x: x["score"], reverse=True)
    world_picks = [s for s in scored if s["score"] >= MIN_GPT_SCORE]

    if not world_picks:
        print(f"\n  No articles scored >= {MIN_GPT_SCORE}. World slot left empty.")
        return

    # ── Step 3: story repeat check ────────────────────────────
    # Load the last 7 days of world articles from Supabase so we can compare
    # today's candidates against them. This prevents the same ongoing story
    # (e.g. Russia/Ukraine, US/Iran talks) from dominating the world slot
    # day after day.
    print(f"\n  {'─'*55}")
    print(f"  STORY REPEAT CHECK (last {STORY_REPEAT_WINDOW_DAYS} days)")
    print(f"  {'─'*55}\n")

    recent_world = fetch_recent_world_articles()
    print(f"  Found {len(recent_world)} world articles from the last {STORY_REPEAT_WINDOW_DAYS} days\n")

    # Filter world_picks to only candidates that aren't repeats.
    # We embed each candidate and compare — see is_repeat_story() for details.
    fresh_picks = []
    forced_pick = None  # fallback: best-scored candidate even if it's a repeat

    for candidate in world_picks:
        is_repeat, matched_title, sim = is_repeat_story(
            candidate["title"], candidate["description"], recent_world
        )
        if is_repeat:
            print(f"  ⚠ REPEAT  [{candidate['source']}] {candidate['title'][:55]}")
            print(f"           → too similar to: '{matched_title[:55]}' (sim={sim:.2f})\n")
            # Save the highest-scored repeat as a fallback in case ALL candidates are repeats.
            # During active crises (war, pandemic) this is common — we don't want to leave
            # the world slot empty just because the biggest story is ongoing.
            if forced_pick is None:
                forced_pick = candidate
        else:
            print(f"  ✓ FRESH   [{candidate['source']}] {candidate['title'][:55]}\n")
            fresh_picks.append(candidate)

    if fresh_picks:
        # Normal path: we have at least one candidate that's a genuinely new story
        world_picks = fresh_picks
        print(f"  {len(fresh_picks)} fresh candidate(s) to try\n")
    else:
        # All candidates are repeats of recent stories (e.g. an active war).
        # Fall back to the highest-scored one rather than leaving the slot empty.
        print(f"  All candidates are repeats — using highest-scored anyway (ongoing crisis mode)\n")
        world_picks = [forced_pick]

    # ── Step 4: try to scrape winner for full body ────────────
    print(f"\n  {'─'*55}")
    print(f"  SCRAPING TOP CANDIDATES FOR FULL BODY")
    print(f"  {'─'*55}\n")

    top = None
    body_text = None

    for candidate in world_picks[:5]:
        print(f"  Trying [{candidate['source']}] {candidate['title'][:60]}")
        body = scrape_jina(candidate["url"])
        if body:
            print(f"  ✓ Scraped successfully ({len(body)} chars)")
            top = candidate
            body_text = body
            break
        else:
            print(f"  ✗ Jina blocked — falling back to description")
            if top is None:
                top = candidate
                body_text = candidate["description"]

    # ── Step 5: save + update briefings ──────────────────────
    print(f"\n  {'─'*55}")
    print(f"  WINNER")
    print(f"  {'─'*55}")
    print(f"  {top['score']}/10 [{top['category']}] [{top['source']}]")
    print(f"  {top['title']}")
    print(f"  {top['reason']}")
    print(f"  Body: {'full article' if body_text != top['description'] else 'description fallback'} ({len(body_text)} chars)\n")

    world_embedding = embed_text(f"{top['title']} {body_text}")

    article_id = insert_world_article(
        top["title"], top["url"], body_text,
        top["source"], top["category"], world_embedding
    )
    if not article_id:
        print("  ✗ Failed to insert world article.")
        return

    print(f"  ✓ Inserted article ID: {article_id}")
    update_briefings_world_per_user(article_id, world_embedding)

    print(f"\n{'=' * 55}")
    print("DONE")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()
