"""
world_ranker.py

Runs after ranker.py, before summarizer.py.
1. Fetches top GDELT stories (last 8 hours)
2. Scrapes each with Jina
3. GPT-scores each for global significance
4. Inserts the #1 article into the articles table
5. Updates all of today's briefings with world_article_ids = [that article id]

Run from backend/:
  python3 workers/world/world_ranker.py
"""

import requests, zipfile, io, csv, os, sys
import numpy as np
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from urllib.parse import urlparse
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_HEADERS = {"Authorization": f"Bearer {JINA_API_KEY}"} if JINA_API_KEY else {}

GDELT_HOURS        = 8
GDELT_FETCH_N      = 15    # candidates to pull from GDELT
MIN_GPT_SCORE      = 6.0   # minimum significance score to include as world article
WORLD_SLOTS        = 1     # how many world articles per briefing
EMBEDDING_MODEL    = "text-embedding-3-small"

# Trusted outlets — all equal. Only stories where GDELT's representative URL
# comes from one of these domains are considered.
TRUSTED_DOMAINS = {
    # Wire services
    "reuters.com", "apnews.com", "afp.com",
    # Major US nationals
    "nytimes.com", "washingtonpost.com", "wsj.com", "bloomberg.com",
    "politico.com", "theatlantic.com", "npr.org", "axios.com",
    "cnn.com", "nbcnews.com", "abcnews.go.com", "cbsnews.com",
    "msnbc.com", "foxnews.com", "usatoday.com", "latimes.com",
    "chicagotribune.com", "bostonglobe.com", "thehill.com",
    "vox.com", "slate.com", "salon.com", "newsweek.com",
    "time.com", "forbes.com", "businessinsider.com",
    "huffpost.com", "thedailybeast.com", "motherjones.com",
    "foreignpolicy.com", "foreignaffairs.com", "defenseone.com",
    # Major international
    "bbc.com", "bbc.co.uk", "theguardian.com", "economist.com",
    "ft.com", "aljazeera.com", "france24.com", "dw.com",
    "spiegel.de", "lemonde.fr",
    # Tech / niche but credible
    "techcrunch.com", "theverge.com", "arstechnica.com",
    "wired.com", "technologyreview.mit.edu",
}
SIMILARITY_CUTOFF  = 0.82  # if world article is this similar to an existing article, skip for that user

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


# ── GDELT ─────────────────────────────────────────────────────────────────────

def get_gdelt_file_urls(hours: int) -> list[str]:
    now = datetime.now(timezone.utc)
    urls = []
    for i in range(hours * 4):
        t = now - timedelta(minutes=15 * i)
        t = t.replace(minute=(t.minute // 15) * 15, second=0, microsecond=0)
        urls.append(f"http://data.gdeltproject.org/gdeltv2/{t.strftime('%Y%m%d%H%M%S')}.export.CSV.zip")
    return list(dict.fromkeys(urls))


def get_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except:
        return ""


def fetch_top_gdelt_stories(hours: int = GDELT_HOURS, top_n: int = GDELT_FETCH_N) -> list[dict]:
    urls = get_gdelt_file_urls(hours)
    print(f"  Fetching {len(urls)} GDELT files ({hours}h window)...")

    aggregated = defaultdict(lambda: {"num_articles": 0, "goldstein": 0, "url": "", "domain": ""})

    total_rows = 0
    trusted_rows = 0

    for i, url in enumerate(urls):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                continue
            z = zipfile.ZipFile(io.BytesIO(r.content))
            lines = z.read(z.namelist()[0]).decode("utf-8").splitlines()
            for row in csv.reader(lines, delimiter="\t"):
                if len(row) < 61:
                    continue
                try:
                    src = row[60]
                    if not src or not src.startswith("http"):
                        continue
                    total_rows += 1
                    domain = get_domain(src)
                    if domain not in TRUSTED_DOMAINS:
                        continue
                    trusted_rows += 1
                    aggregated[src]["num_articles"] += int(row[33]) if row[33] else 0
                    aggregated[src]["goldstein"]     = float(row[30]) if row[30] else 0
                    aggregated[src]["url"]           = src
                    aggregated[src]["domain"]        = domain
                except:
                    continue
            print(f"  file {i+1}/{len(urls)} done", end="\r")
        except:
            continue

    print(f"\n  Total URLs seen: {total_rows} | From trusted outlets: {trusted_rows} | Unique trusted stories: {len(aggregated)}")
    top = sorted(aggregated.values(), key=lambda x: x["num_articles"], reverse=True)
    return top[:top_n]


# ── Jina ──────────────────────────────────────────────────────────────────────

def scrape_jina(url: str) -> tuple[str | None, str | None]:
    try:
        r = requests.get(f"https://r.jina.ai/{url}", headers=JINA_HEADERS, timeout=20)
        text = r.text.strip()

        blocked = r.status_code in [451, 403] or any(x in text.lower() for x in [
            "securitycompromiseerror", "authenticationfailed", "paywall", "subscribe to read"
        ])
        if blocked:
            return None, None

        title = ""
        body_lines = []
        in_body = False
        for line in text.splitlines():
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            if line.startswith("Markdown Content:"):
                in_body = True
                continue
            if in_body and line.strip():
                body_lines.append(line.strip())
            if len(" ".join(body_lines)) > 3000:
                break

        body = " ".join(body_lines)[:3000]
        return title or None, body or None
    except:
        return None, None


# ── GPT scoring ───────────────────────────────────────────────────────────────

def score_significance(title: str, body: str) -> tuple[float | None, str, str]:
    content = f"Title: {title}\n\n{body[:1200]}"
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


# ── Supabase ──────────────────────────────────────────────────────────────────

def insert_world_article(title: str, url: str, body_text: str, category: str, embedding: np.ndarray | None) -> str | None:
    """
    Inserts the world article into the articles table (upsert on URL as guardian_id).
    Saves embedding so similarity checks work immediately.
    Returns the article's UUID.
    """
    payload = {
        "title":        title,
        "url":          url,
        "source":       f"gdelt_world_{category}",
        "body_text":    body_text,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "guardian_id":  url,
    }
    if embedding is not None:
        payload["embedding"] = embedding.tolist()

    result = (
        supabase.table("articles")
        .upsert(payload, on_conflict="guardian_id")
        .execute()
    )
    if result.data:
        return result.data[0]["id"]

    fetch = supabase.table("articles").select("id").eq("guardian_id", url).single().execute()
    return fetch.data["id"] if fetch.data else None


def update_briefings_world_per_user(article_id: str, world_embedding: np.ndarray | None):
    """
    Updates each user's briefing individually.
    Skips the world slot if the world article is too similar to anything
    already in their interest or learning picks (same story, different source).
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
                emb = np.array(art["embedding"], dtype=np.float32)
                sim = cosine_similarity(world_embedding, emb)
                if sim >= SIMILARITY_CUTOFF:
                    too_similar = True
                    print(f"  ⚠ Skipping world for user {b['user_id'][:8]}... (similarity {sim:.2f} with existing article)")
                    break

        if too_similar:
            skipped += 1
            continue

        supabase.table("briefings").update(
            {"world_article_ids": [article_id]}
        ).eq("id", b["id"]).execute()
        added += 1

    print(f"  ✓ World article added to {added} briefings, skipped {skipped} (already covered)")


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("\n" + "=" * 55)
    print("WORLD RANKER")
    print("=" * 55 + "\n")

    stories = fetch_top_gdelt_stories()

    print(f"\n  Scoring {len(stories)} candidates...\n")

    results = []
    for i, story in enumerate(stories, 1):
        url = story["url"]
        print(f"  [{i}/{len(stories)}] [{story.get('domain','?')}] {url[:55]}")

        title, body = scrape_jina(url)
        if not title or not body:
            print(f"         → Jina blocked/failed, skipping")
            continue

        score, reason, category = score_significance(title, body)
        if score is None:
            print(f"         → GPT failed, skipping")
            continue

        print(f"         → {score}/10 [{category}] {reason[:60]}")
        results.append({
            "score":    score,
            "title":    title,
            "url":      url,
            "body":     body,
            "reason":   reason,
            "category": category,
        })

    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)

    # Filter to significant stories
    world_picks = [r for r in results if r["score"] >= MIN_GPT_SCORE]

    if not world_picks:
        print(f"\n  No articles scored >= {MIN_GPT_SCORE}. World slot left empty.")
        return

    top = world_picks[0]
    print(f"\n  TOP WORLD ARTICLE: {top['score']}/10 [{top['category']}]")
    print(f"  {top['title']}")
    print(f"  {top['reason']}\n")

    print(f"  Embedding world article...")
    world_embedding = embed_text(f"{top['title']} {top['body']}")

    article_id = insert_world_article(top["title"], top["url"], top["body"], top["category"], world_embedding)
    if not article_id:
        print("  ✗ Failed to insert world article into database.")
        return

    print(f"  ✓ Inserted article ID: {article_id}")

    update_briefings_world_per_user(article_id, world_embedding)

    print(f"\n{'=' * 55}")
    print("DONE")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()
