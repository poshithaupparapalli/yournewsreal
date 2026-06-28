from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import supabase

router = APIRouter()


class UpdateEmailData(BaseModel):
    email: str


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    result = supabase.table("users").select(
        "id, name, email, interests_raw, learning_goals_raw, created_at"
    ).eq("id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return result.data[0]


@router.patch("/users/{user_id}/email")
async def update_email(user_id: str, data: UpdateEmailData):
    # Check the new email isn't already taken by someone else
    existing = supabase.table("users").select("id").eq("email", data.email).neq("id", user_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already in use")

    result = supabase.table("users").update({"email": data.email}).eq("id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "email": data.email}