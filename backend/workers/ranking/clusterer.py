"""
clusterer.py

Runs once per day after article_embedder.py.
Fetches all article embeddings, runs Leiden community detection,
and writes a cluster_id back to each article in Supabase.

No user logic here — purely article-side processing.

Run from backend/:
  python workers/clusterer.py

Install deps:
  pip install igraph leidenalg numpy
"""

import os
import sys
import ast
import numpy as np
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

# ─────────────────────────────────────────────────────────────
# CONFIG
# Lower = more/smaller clusters, Higher = fewer/broader clusters
# 0.40 works well for ~200-2000 news articles
SIMILARITY_THRESHOLD = 0.40
# ─────────────────────────────────────────────────────────────


def fetch_articles() -> list[dict]:
    """
    Fetches all articles that have embeddings.
    Resets cluster_id on each run so clustering is always fresh.
    """
    print("Fetching articles with embeddings...")
    result = (
        supabase.table("articles")
        .select("id, embedding")
        .not_.is_("embedding", "null")
        .execute()
    )
    print(f"  Found {len(result.data)} articles")
    return result.data


def parse_embeddings(articles: list[dict]) -> np.ndarray:
    """
    Converts embeddings from Supabase (may come as strings) to numpy array.
    """
    return np.array([
        ast.literal_eval(a["embedding"]) if isinstance(a["embedding"], str) else a["embedding"]
        for a in articles
    ], dtype=np.float32)


def run_leiden(embeddings: np.ndarray) -> list[int]:
    """
    Builds a cosine similarity graph and runs Leiden community detection.
    Returns a list mapping each article index to a cluster_id integer.
    """
    import igraph as ig
    import leidenalg

    print("Building similarity graph...")
    n = len(embeddings)

    # Normalise for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / np.clip(norms, 1e-10, None)
    sim_matrix = np.dot(normed, normed.T)

    edges, weights = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if sim_matrix[i][j] >= SIMILARITY_THRESHOLD:
                edges.append((i, j))
                weights.append(float(sim_matrix[i][j]))

    print(f"  {len(edges)} edges above threshold {SIMILARITY_THRESHOLD}")

    graph = ig.Graph(n=n, edges=edges)
    if weights:
        graph.es["weight"] = weights

    print("Running Leiden clustering...")
    partition = leidenalg.find_partition(
        graph,
        leidenalg.ModularityVertexPartition,
        weights="weight" if weights else None
    )
    print(f"  Found {len(partition)} clusters")
    return partition.membership


def save_cluster_ids(articles: list[dict], cluster_ids: list[int]):
    """
    Writes cluster_id back to each article row in Supabase.
    """
    print("Saving cluster IDs to Supabase...")
    saved = 0

    for article, cluster_id in zip(articles, cluster_ids):
        supabase.table("articles").update(
            {"cluster_id": cluster_id}
        ).eq("id", article["id"]).execute()
        saved += 1

    print(f"  Updated {saved} articles")


def run():
    print("\n" + "=" * 55)
    print("CLUSTERER")
    print("=" * 55 + "\n")

    articles = fetch_articles()
    if len(articles) < 5:
        print("Need at least 5 articles with embeddings. Exiting.")
        return

    embeddings = parse_embeddings(articles)
    print(f"  Embedding matrix: {embeddings.shape}\n")

    cluster_ids = run_leiden(embeddings)
    save_cluster_ids(articles, cluster_ids)

    print(f"\n{'=' * 55}")
    print(f"DONE — {len(set(cluster_ids))} clusters assigned across {len(articles)} articles")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    run()