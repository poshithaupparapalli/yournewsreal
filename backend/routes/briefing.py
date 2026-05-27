from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import supabase

router = APIRouter()


@router.get("/briefing/{user_id}")
async def get_briefing(user_id: str):
    today = datetime.now(timezone.utc).date().isoformat()

    # Get today's briefing for this user
    briefing = (
        supabase.table("briefings")
        .select("interest_article_ids, learning_article_ids, world_article_ids")
        .eq("user_id", user_id)
        .eq("date", today)
        .single()
        .execute()
    )

    if not briefing.data:
        raise HTTPException(status_code=404, detail="No briefing found for today")

    interest_ids = briefing.data.get("interest_article_ids") or []
    learning_ids = briefing.data.get("learning_article_ids") or []
    world_ids    = briefing.data.get("world_article_ids") or []

    all_ids = interest_ids + learning_ids + world_ids
    if not all_ids:
        raise HTTPException(status_code=404, detail="Briefing is empty")

    # Fetch all articles in one query
    articles_result = (
        supabase.table("articles")
        .select("id, title, source, url, llm_summary")
        .in_("id", all_ids)
        .execute()
    )

    articles_by_id = {a["id"]: a for a in articles_result.data}

    def format_article(article_id, tag):
        a = articles_by_id.get(article_id)
        if not a:
            return None
        return {
            "id":      a["id"],
            "title":   a["title"],
            "source":  a["source"].replace("_", " ").title(),
            "summary": a["llm_summary"] or "",
            "url":     a["url"],
            "tag":     tag,
        }

    interests = [x for x in [format_article(i, "your stories")       for i in interest_ids] if x]
    learning  = [x for x in [format_article(i, "something to learn") for i in learning_ids]  if x]
    world     = [x for x in [format_article(i, "the world today")    for i in world_ids]     if x]

    return {
        "interests": interests,
        "learning":  learning,
        "world":     world,
    }
