from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import supabase

router = APIRouter()


class FeedbackData(BaseModel):
    user_id: str
    score: int
    text: str = ""


@router.post("/feedback")
async def submit_feedback(data: FeedbackData):
    today = datetime.now(timezone.utc).date().isoformat()
    supabase.table("feedback").insert({
        "user_id":    data.user_id,
        "date":       today,
        "score":      data.score,
        "text":       data.text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return {"success": True}
