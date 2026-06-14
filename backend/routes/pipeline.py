from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter()


def _run_for_user(user_id: str):
    from workers.ranking import ranker
    from workers.ranking import world_ranker
    from workers.ranking import summarizer
    from workers.scrapers import guardian_world_scraper

    print(f"\n=== ON-DEMAND PIPELINE for user {user_id[:8]}... ===")
    ranker.run_for_user(user_id)
    guardian_world_scraper.run()
    world_ranker.run_for_user(user_id)  # fixed: scoped to this user only
    summarizer.run()                    # safe: skips already-summarized articles
    print(f"=== DONE for user {user_id[:8]}... ===\n")


@router.post("/run-pipeline/{user_id}")
async def run_pipeline(
    user_id: str,
    background_tasks: BackgroundTasks,
    x_pipeline_secret: str = Header(None)
):
    if x_pipeline_secret != os.getenv("PIPELINE_SECRET"):
        raise HTTPException(status_code=403, detail="Forbidden")
    background_tasks.add_task(_run_for_user, user_id)
    return {"status": "started"}


@router.get("/briefing-ready/{user_id}")
async def briefing_ready(user_id: str):
    from database.connection import supabase
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date().isoformat()
    result = (
        supabase.table("briefings")
        .select("id")
        .eq("user_id", user_id)
        .eq("date", today)
        .execute()
    )
    return {"ready": bool(result.data)}