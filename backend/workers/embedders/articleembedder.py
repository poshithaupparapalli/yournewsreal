"""
article_embedder.py

Fetches all unembedded articles from Supabase, generates embeddings
for each using OpenAI, and stores the vector back on the articles table.

Run manually with: python workers/embedders/article_embedder.py
Will eventually run right after the scraper finishes each morning.
"""

import os
import time
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Go up two levels (embedders/ -> workers/ -> backend/) so we can import database/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import supabase

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────────────────────
# CONFIG
EMBEDDING_MODEL = "text-embedding-3-small"  # cheap and accurate enough for news
BATCH_SIZE = 20  # how many articles to embed per API call
                 # OpenAI supports up to 2048 inputs per batch but 20 is safe
# ─────────────────────────────────────────────────────────────


def get_unembedded_articles() -> list[dict]:
    """
    Fetches all articles that don't have an embedding yet.
    Only pulls id and body_preview — no need to fetch full body_text.
    """
    result = (
        supabase.table("articles")
        .select("id, title, body_preview")
        .is_("embedding", "null")
        .execute()
    )
    return result.data


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Sends a batch of texts to OpenAI and returns a list of vectors.
    Batching is more efficient than one API call per article.
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    # Sort by index to make sure order matches input order
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]


def save_embedding(article_id: str, embedding: list[float]):
    """
    Saves the embedding vector back to the articles table.
    Updates only the embedding column — leaves everything else untouched.
    """
    supabase.table("articles").update(
        {"embedding": embedding}
    ).eq("id", article_id).execute()


def run():
    print("\n" + "=" * 60)
    print("ARTICLE EMBEDDER")
    print("=" * 60)

    articles = get_unembedded_articles()

    if not articles:
        print("\nNo unembedded articles found. Exiting.")
        return

    print(f"\nFound {len(articles)} articles to embed")
    print(f"Model:      {EMBEDDING_MODEL}")
    print(f"Batch size: {BATCH_SIZE}\n")

    embedded = 0
    failed = 0

    # Process in batches
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i: i + BATCH_SIZE]

        # Filter out any articles with empty body_preview
        valid = [a for a in batch if a.get("body_preview")]
        skipped = len(batch) - len(valid)
        if skipped:
            print(f"  ⚠ Skipped {skipped} articles with empty body_preview")

        if not valid:
            continue

        texts = [a["body_preview"] for a in valid]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(articles) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Embedding batch {batch_num}/{total_batches} ({len(valid)} articles)...")

        try:
            vectors = embed_batch(texts)

            # Save each vector back to its article row
            for article, vector in zip(valid, vectors):
                try:
                    save_embedding(article["id"], vector)
                    embedded += 1
                except Exception as e:
                    print(f"  ⚠ Failed to save embedding for {article['id']}: {e}")
                    failed += 1

        except Exception as e:
            print(f"  ⚠ Batch {batch_num} failed: {e}")
            failed += len(valid)

        # Small pause between batches to be respectful to the API
        time.sleep(0.2)

    print(f"\n" + "=" * 60)
    print(f"DONE")
    print(f"  Embedded: {embedded}")
    print(f"  Failed:   {failed}")
    print("=" * 60)


if __name__ == "__main__":
    run()