from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt
import sys
import os
from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import supabase
from workers.embedders.userembedder import embed_text, save_user_embeddings

router = APIRouter()


class OnboardingData(BaseModel):
    name: str
    email: str
    password: str
    interests: str        # raw free text e.g. "Jensen Huang, NVIDIA, Formula 1"
    learning_goals: str   # raw free text e.g. "geopolitics, quantum computing"


class LoginData(BaseModel):
    email: str
    password: str


@router.post("/onboarding")
async def onboarding(data: OnboardingData):

    # Check if email already exists
    existing = supabase.table("users").select("id").eq("email", data.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    # Save user row with raw interest text
    user_result = supabase.table("users").insert({
        "name":               data.name,
        "email":              data.email,
        "password_hash":      password_hash,
        "interests_raw":      data.interests,
        "learning_goals_raw": data.learning_goals,
    }).execute()

    user_id = user_result.data[0]["id"]

    # Embed both onboarding responses immediately after signup
    # This means their first briefing can be ranked right away
    """
    try:
        interest_vector      = embed_text(data.interests)
        learning_vector      = embed_text(data.learning_goals)
        save_user_embeddings(user_id, interest_vector, learning_vector)
    except Exception as e:
        import traceback
        print(f"WARNING: embedding failed for user {user_id}")
        print(traceback.format_exc())
    """
    
    try:
        interest_vector      = embed_text(data.interests)
        learning_vector      = embed_text(data.learning_goals)
        save_user_embeddings(user_id, interest_vector, learning_vector)
    except Exception as e:
        # Don't fail the signup if embedding fails — user is still created
        # Embedder will pick them up on its next run
        print(f"Warning: embedding failed for user {user_id}: {e}")

    return {"success": True, "user_id": user_id}
    

@router.post("/login")
async def login(data: LoginData):

    # Look up user by email
    result = supabase.table("users_waitlist").select(
        "id, name, email, password_hash"
    ).eq("email", data.email).execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = result.data[0]

    # Verify password
    if not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "success": True,
        "user_id": user["id"],
        "name":    user["name"],
        "email":   user["email"],
    }