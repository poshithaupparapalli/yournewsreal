"""
userembedder.py is made so that we can create vectors for both the user's entries on onboarding form to start the ranking process
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

# CONFIG
EMBEDDING_MODEL = "text-embedding-3-small"  


def get_unembedded_users() -> list[dict]:
    """
    right after user has signed up, will call this function to retrieve the newly inputed user responses for our onboarding form
    """
    result = (
        supabase.table("users")
        .select("id, interests_raw, learning_goals_raw")
        .is_("interests_raw_vector", "null")
        .not_.is_("interests_raw", "null")
        .execute()
    )
    return result.data


def embed_text(text: str) -> list[float]:
    """
    calls api to create single vector for each text input
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text.strip()
    )
    return response.data[0].embedding


def save_user_embeddings(user_id: str, user_interests: list[float], user_learning_goals: list[float]):
    #Saves the embedding vector back to the articles table.
    supabase.table("users").update(
        {"interests_raw_vector": user_interests,
        "learning_goals_raw_vector": user_learning_goals
    }).eq("id", user_id).execute()



def run():
    print("\n" + "=" * 60)
    print("USER EMBEDDER")
    print("=" * 60)
 
    users = get_unembedded_users()
 
    if not users:
        print("\nNo unembedded users found. Exiting.")
        return
 
    print(f"\nFound {len(users)} user(s) to embed")
    print(f"Model: {EMBEDDING_MODEL}\n")
 
    embedded = 0
    failed = 0
 
    for user in users:
        user_id = user["id"]
        interests = user.get("interests_raw", "")
        learning_goals = user.get("learning_goals_raw", "")
 
        try:
            print(f"  Embedding user {user_id}...")
 
            interest_vector = embed_text(interests)
            learning_vector = embed_text(learning_goals) if learning_goals else embed_text("")
 
            save_user_embeddings(user_id, interest_vector, learning_vector)
            embedded += 1
            print(f"  ✓ Done")
 
        except Exception as e:
            print(f"  ⚠ Failed for user {user_id}: {e}")
            failed += 1
 
    print(f"\n" + "=" * 60)
    print(f"DONE")
    print(f"  Embedded: {embedded}")
    print(f"  Failed:   {failed}")
    print("=" * 60)


if __name__ == "__main__":
    run()