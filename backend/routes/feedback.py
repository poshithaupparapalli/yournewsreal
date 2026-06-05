from fastapi import APIRouter, Request
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

@router.post("/webhooks/resend")
async def resend_webhook(request: Request):
    payload = await request.json()

    event_type = payload.get("type")
    to_list = payload.get("data", {}).get("to", [])

    if not to_list:
        return {"ok": True}
    
    email = to_list[0]

    if event_type == "email.opened":
        db_event = "email_opened"
    elif event_type == "email.clicked":
        db_event = "email_clicked"
    else:
        return {"ok": True}

    result = supabase.table("users").select("id").eq("email", email).execute()

    if not result.data:
        return {"ok": True}

    user_id = result.data[0]["id"]

    supabase.table("feedback_events").insert({
        "user_id":     user_id,
        "event_type":  db_event,
        "occurred_at": datetime.now(timezone.utc).isoformat()
    }).execute()

    return {"ok": True}



