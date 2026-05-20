"""
ranker.py

Runs once per day after clusterer.py.
For each user:
  1. Scores all articles against their interest_vector (5 slots)
  2. Scores all articles against their learning_vector (1 slot)
  3. Writes results to briefings table as three separate arrays
     (world_article_ids filled later by world importance module)

Run from backend/:
  python workers/ranking/ranker.py
"""

import os
import sys
import ast
import numpy as np
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

# ─────────────────────────────────────────────────────────────
# CONFIG
MIN_SCORE       = 0.15   # minimum cosine similarity to include an article
MAX_PER_CLUSTER = 2      # max articles per cluster across the whole briefing
INTEREST_SLOTS  = 5      # articles from interest_vector
LEARNING_SLOTS  = 1      # articles from learning_vector
# world slots handled separately by world importance module
# ─────────────────────────────────────────────────────────────


def fetch_users() -> list[dict]:
    """
    Fetches all users who have both vectors embedded.
    """
    result = (
        supabase.table("users_waitlist")
        .select("id, interests_raw_vector, learning_goals_raw_vector")
        .not_.is_("interests_raw_vector", "null")
        .not_.is_("learning_goals_raw_vector", "null")
        .execute()
    )
    print(f"  Found {len(result.data)} users")
    return result.data


def fetch_articles() -> list[dict]:
    """
    Fetches all articles with embeddings and cluster assignments.
    """
    result = (
        supabase.table("articles")
        .select("id, title, source, cluster_id, embedding")
        .not_.is_("embedding", "null")
        .not_.is_("cluster_id", "null")
        .execute()
    )
    print(f"  Found {len(result.data)} articles")
    return result.data


def parse_vector(v) -> np.ndarray:
    """
    Parses a vector from Supabase — handles both string and list formats.
    """
    if isinstance(v, str):
        return np.array(ast.literal_eval(v), dtype=np.float32)
    return np.array(v, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Computes cosine similarity between two vectors.
    """
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def select_articles(
    articles: list[dict],
    article_embeddings: np.ndarray,
    user_vector: np.ndarray,
    n_slots: int,
    existing_cluster_counts: dict = None
) -> tuple[list[dict], dict]:
    """
    Scores all articles against a user vector and selects top articles
    using cluster-aware deduplication.

    existing_cluster_counts lets us pass in cluster usage from a previous
    selection round (e.g. interest picks) so learning picks don't repeat
    the same clusters.

    Returns (selected_articles, updated_cluster_counts).
    """
    cluster_counts = existing_cluster_counts.copy() if existing_cluster_counts else {}

    # Score every article
    scored = []
    for i, article in enumerate(articles):
        score = cosine_similarity(article_embeddings[i], user_vector)
        scored.append((score, article))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)

    # DEBUG — print top 5 scores to see what range we're working with
    print(f"    Top 5 scores: {[round(s, 4) for s, _ in scored[:5]]}")

    selected = []

    for score, article in scored:
        # Stop if below minimum threshold
        if score < MIN_SCORE:
            break

        cluster_id = article.get("cluster_id")

        # Enforce per-cluster cap across both interest and learning picks
        if cluster_counts.get(cluster_id, 0) >= MAX_PER_CLUSTER:
            continue

        selected.append({**article, "score": round(score, 4)})
        cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1

        if len(selected) >= n_slots:
            break

    return selected, cluster_counts


def build_briefing(
    user: dict,
    articles: list[dict],
    article_embeddings: np.ndarray
) -> tuple[list[str], list[str]]:
    """
    Runs selection for interests then learning goals.
    Shares cluster_counts between both runs so they don't overlap.
    Returns (interest_ids, learning_ids).
    """
    interest_vector = parse_vector(user["interests_raw_vector"])
    learning_vector = parse_vector(user["learning_goals_raw_vector"])

    # Run interest selection first
    interest_picks, cluster_counts = select_articles(
        articles, article_embeddings, interest_vector, INTEREST_SLOTS
    )

    # CHANGE 1: do NOT pass cluster_counts from interest picks into learning.
    # The old code shared cluster_counts, which meant every cluster the interest
    # round used was already at MAX_PER_CLUSTER=2 — so learning could never pick
    # anything. Learning now starts with its own fresh cluster counts.
    #
    # CHANGE 2: request LEARNING_SLOTS + INTEREST_SLOTS candidates (6 total)
    # instead of just LEARNING_SLOTS (1). If we only asked for 1 and that 1
    # article was already in interest_picks, deduplication below would discard
    # it and leave 0 learning articles. The extra buffer means even if all 5
    # interest articles appear in the top learning results, there's still a
    # unique 6th one available.
    learning_candidates, _ = select_articles(
        articles, article_embeddings, learning_vector,
        LEARNING_SLOTS + INTEREST_SLOTS,
    )

    interest_ids = [a["id"] for a in interest_picks]
    seen = set(interest_ids)

    learning_ids = []
    for a in learning_candidates:
        if a["id"] not in seen:
            learning_ids.append(a["id"])
            seen.add(a["id"])
            # CHANGE 3: stop as soon as we have enough learning articles.
            # Without this break we'd loop over all 6 candidates and
            # collect more than LEARNING_SLOTS articles.
            if len(learning_ids) >= LEARNING_SLOTS:
                break

    return interest_ids, learning_ids


def save_briefing(user_id: str, interest_ids: list[str], learning_ids: list[str]):
    """
    Saves interest and learning article IDs to the briefings table.
    world_article_ids is left empty — filled later by world importance module.
    Uses upsert on user_id + date so re-running is safe.
    """
    today = datetime.now(timezone.utc).date().isoformat()

    supabase.table("briefings").upsert({
        "user_id":              user_id,
        "date":                 today,
        "interest_article_ids": interest_ids,
        "learning_article_ids": learning_ids,
        "world_article_ids":    [],
        "sent_at":              None,
    }, on_conflict="user_id,date").execute()


def run():
    print("\n" + "=" * 55)
    print("RANKER")
    print("=" * 55 + "\n")

    users    = fetch_users()
    articles = fetch_articles()

    if not users:
        print("No users with embeddings found. Exiting.")
        return
    if not articles:
        print("No articles with embeddings and cluster IDs found. Exiting.")
        return

    print(f"\nSlots per user: {INTEREST_SLOTS} interest + {LEARNING_SLOTS} learning + 3 world\n")

    # Parse all article embeddings once — reused for every user
    article_embeddings = np.array([
        parse_vector(a["embedding"]) for a in articles
    ], dtype=np.float32)

    ranked = 0
    failed = 0

    for user in users:
        user_id = user["id"]
        try:
            interest_ids, learning_ids = build_briefing(
                user, articles, article_embeddings
            )
            save_briefing(user_id, interest_ids, learning_ids)
            ranked += 1
            print(f"  ✓ User {user_id[:8]}... → {len(interest_ids)} interest, {len(learning_ids)} learning")
        except Exception as e:
            print(f"  ✗ User {user_id[:8]}... failed: {e}")
            failed += 1

    print(f"\n{'=' * 55}")
    print(f"DONE")
    print(f"  Ranked: {ranked} users")
    print(f"  Failed: {failed} users")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()