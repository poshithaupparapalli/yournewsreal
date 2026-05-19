"""
cluster_plot.py

Fetches article embeddings, clusters with Leiden, plots with matplotlib.

Install deps:
  pip install umap-learn igraph leidenalg matplotlib numpy

Run from backend/:
  python workers/cluster_plot.py
"""

import os
import sys
import ast
import numpy as np
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import supabase

load_dotenv()

SIMILARITY_THRESHOLD = 0.45


def fetch_articles():
    print("Fetching articles...")
    result = (
        supabase.table("articles")
        .select("title, source, embedding")
        .not_.is_("embedding", "null")
        .execute()
    )
    print(f"  Found {len(result.data)} articles")
    return result.data


def parse_embeddings(articles):
    return np.array([
        ast.literal_eval(a["embedding"]) if isinstance(a["embedding"], str) else a["embedding"]
        for a in articles
    ], dtype=np.float32)


def cluster(embeddings):
    import igraph as ig
    import leidenalg

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / np.clip(norms, 1e-10, None)
    sim = np.dot(normed, normed.T)

    edges, weights = [], []
    n = len(embeddings)
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i][j] >= SIMILARITY_THRESHOLD:
                edges.append((i, j))
                weights.append(float(sim[i][j]))

    g = ig.Graph(n=n, edges=edges)
    if weights:
        g.es["weight"] = weights

    partition = leidenalg.find_partition(
        g, leidenalg.ModularityVertexPartition,
        weights="weight" if weights else None
    )
    print(f"  Found {len(partition)} clusters")
    return partition.membership


def reduce_2d(embeddings):
    import umap
    print("Running UMAP (~30s)...")
    return umap.UMAP(n_components=2, random_state=42).fit_transform(embeddings)


def plot(coords, cluster_ids, articles):
    import plotly.graph_objects as go
    import plotly.io as pio

    n_clusters = max(cluster_ids) + 1
    fig = go.Figure()

    for cid in range(n_clusters):
        idx = [i for i, c in enumerate(cluster_ids) if c == cid]
        fig.add_trace(go.Scatter(
            x=[coords[i][0] for i in idx],
            y=[coords[i][1] for i in idx],
            mode="markers",
            name=f"Cluster {cid} ({len(idx)})",
            text=[
                f"<b>{articles[i]['title']}</b><br>{articles[i]['source']}"
                for i in idx
            ],
            hovertemplate="%{text}<extra></extra>",
            marker=dict(size=8, opacity=0.85),
        ))

    fig.update_layout(
        title=f"{len(articles)} articles — {n_clusters} clusters",
        xaxis_title="UMAP 1",
        yaxis_title="UMAP 2",
        hovermode="closest",
        height=800,
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(title="Cluster", itemsizing="constant"),
    )

    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "cluster_plot.html"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pio.write_html(fig, output_path)
    print(f"\nSaved to: {output_path}")
    print("Opening in browser...")
    import webbrowser
    webbrowser.open(f"file://{output_path}")


def run():
    articles = fetch_articles()
    embeddings = parse_embeddings(articles)
    print(f"  Embedding matrix: {embeddings.shape}")
    cluster_ids = cluster(embeddings)
    coords = reduce_2d(embeddings)
    plot(coords, cluster_ids, articles)


if __name__ == "__main__":
    run()