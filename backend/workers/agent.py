# agent.py
"""
AI agent that replaces pipeline.py.

Instead of running fixed steps, Claude observes the current state of
the database and decides which steps to run, in what order, and
whether to skip any — just like a smart intern who checks what
needs doing before starting work.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
import anthropic

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Set to True via --dry-run flag. When True, tools are described but never executed.
DRY_RUN = False

# Each tool is a dict that Claude reads to understand what it can do.
# The "description" is the most important part — it's what Claude uses
# to decide whether to call this tool. Write it like you're explaining
# the function to a smart colleague who can't see the code.

TOOLS = [
    {
        "name": "check_pipeline_state",
        "description": (
            "Observe the current state of the database before deciding what to run. "
            "Returns counts of: unembedded articles, unclustered articles, "
            "article_links not yet fetched, briefings for today, and articles "
            "without summaries. Always call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},   # no parameters — it just reads state
            "required": []
        }
    },
    {
        "name": "reset_tables",
        "description": (
            "Clears the briefings, world_candidates, and articles tables to start "
            "fresh. Only call this at the very beginning of a new daily pipeline run, "
            "never mid-run."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "run_guardian_scraper",
        "description": "Fetches today's Guardian articles and saves them to the articles table.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_jina_fetcher",
        "description": (
            "Fetches full text for RSS article links that haven't been fetched yet. "
            "Only useful if there are unfetched links in article_links. Skip if count is 0."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_embedder",
        "description": (
            "Generates embeddings for all articles that don't have one yet. "
            "Must run before clustering or ranking."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_clusterer",
        "description": (
            "Groups articles into topic clusters using Leiden community detection. "
            "Must run after embedder, before ranker."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_ranker",
        "description": (
            "Scores articles against each user's interest and learning vectors and "
            "writes personalized briefings. Must run after clusterer."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_world_scraper",
        "description": "Fetches world news candidates from Guardian.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_world_ranker",
        "description": (
            "Picks the top world article for each user and adds it to their briefing. "
            "Must run after world_scraper and ranker."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_summarizer",
        "description": (
            "Generates LLM summaries for all articles in today's briefings that don't "
            "have one yet. Must run after ranker. Skip if all articles are already summarized."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "clear_article_links",
        "description": (
            "Deletes all rows from article_links now that they've been fetched and saved. "
            "Only call this at the very end, after summarizer."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "finish",
        "description": (
            "Call this when all necessary steps are complete. "
            "Include a summary of what was done and what was skipped."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "What steps ran, what was skipped, and why."
                }
            },
            "required": ["summary"]
        }
    }
]

# ─────────────────────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# Each function here corresponds to one tool in the TOOLS list above.
# When Claude picks a tool, we look up the matching function and call it.
# ─────────────────────────────────────────────────────────────

def check_pipeline_state() -> dict:
    """
    Reads the database and returns a snapshot of what needs doing.
    This is what the agent uses to observe before it decides anything.
    """
    from database.connection import supabase

    # Count articles without embeddings
    unembedded = supabase.table("articles") \
        .select("id", count="exact") \
        .is_("embedding", "null") \
        .execute()

    # Count articles without cluster assignments
    unclustered = supabase.table("articles") \
        .select("id", count="exact") \
        .is_("cluster_id", "null") \
        .not_.is_("embedding", "null") \
        .execute()

    # Count RSS links that haven't been fetched yet
    unfetched_links = supabase.table("article_links") \
        .select("id", count="exact") \
        .eq("fetched", False) \
        .execute()

    # Count briefings created today
    today = datetime.now(timezone.utc).date().isoformat()
    todays_briefings = supabase.table("briefings") \
        .select("id", count="exact") \
        .eq("date", today) \
        .execute()

    # Count articles in today's briefings that still need summaries
    briefings_data = supabase.table("briefings") \
        .select("interest_article_ids, learning_article_ids, world_article_ids") \
        .eq("date", today) \
        .execute()

    # Flatten all article IDs from today's briefings
    all_briefing_ids = []
    for b in (briefings_data.data or []):
        all_briefing_ids += (b.get("interest_article_ids") or [])
        all_briefing_ids += (b.get("learning_article_ids") or [])
        all_briefing_ids += (b.get("world_article_ids") or [])

    unique_ids = list(set(all_briefing_ids))

    unsummarized = 0
    if unique_ids:
        result = supabase.table("articles") \
            .select("id", count="exact") \
            .in_("id", unique_ids) \
            .is_("llm_summary", "null") \
            .execute()
        unsummarized = result.count or 0

    state = {
        "unembedded_articles":   unembedded.count or 0,
        "unclustered_articles":  unclustered.count or 0,
        "unfetched_rss_links":   unfetched_links.count or 0,
        "todays_briefings":      todays_briefings.count or 0,
        "unsummarized_articles": unsummarized,
    }

    print(f"  Pipeline state: {json.dumps(state, indent=2)}")
    return state

def tool_reset_tables() -> dict:
    from database.connection import supabase
    supabase.rpc("truncate_daily_tables").execute()
    return {"status": "ok", "message": "Tables reset"}


def tool_run_guardian_scraper() -> dict:
    from workers.scrapers import test_guardian2
    test_guardian2.run()
    return {"status": "ok", "message": "Guardian scraper complete"}


def tool_run_jina_fetcher() -> dict:
    from workers.scrapers import jina
    jina.run()
    return {"status": "ok", "message": "Jina fetcher complete"}


def tool_run_embedder() -> dict:
    from workers.embedders import articleembedder
    articleembedder.run()
    return {"status": "ok", "message": "Embedder complete"}


def tool_run_clusterer() -> dict:
    from workers.ranking import clusterer
    clusterer.run()
    return {"status": "ok", "message": "Clusterer complete"}


def tool_run_ranker() -> dict:
    from workers.ranking import ranker
    ranker.run()
    return {"status": "ok", "message": "Ranker complete"}


def tool_run_world_scraper() -> dict:
    from workers.scrapers import guardian_world_scraper
    guardian_world_scraper.run()
    return {"status": "ok", "message": "World scraper complete"}


def tool_run_world_ranker() -> dict:
    from workers.ranking import world_ranker
    world_ranker.run()
    return {"status": "ok", "message": "World ranker complete"}


def tool_run_summarizer() -> dict:
    from workers.ranking import summarizer
    summarizer.run()
    return {"status": "ok", "message": "Summarizer complete"}


def tool_clear_article_links() -> dict:
    from database.connection import supabase
    supabase.rpc("truncate_article_links").execute()
    return {"status": "ok", "message": "Article links cleared"}

def run_tool(tool_name: str, tool_input: dict) -> str:
    # In dry-run mode, skip everything except check_pipeline_state (read-only).
    # Claude still sees realistic-looking results so it plans the full sequence.
    if DRY_RUN and tool_name not in ("check_pipeline_state", "finish"):
        print(f"  [DRY RUN] would have run: {tool_name}")
        return json.dumps({"status": "ok", "message": f"[DRY RUN] {tool_name} skipped"})
    """
    Called whenever Claude picks a tool. Routes the tool name to the
    matching Python function and returns the result as a string.
    Claude reads this string to inform its next decision.
    """
    dispatch = {
        "check_pipeline_state": check_pipeline_state,
        "reset_tables":         tool_reset_tables,
        "run_guardian_scraper": tool_run_guardian_scraper,
        "run_jina_fetcher":     tool_run_jina_fetcher,
        "run_embedder":         tool_run_embedder,
        "run_clusterer":        tool_run_clusterer,
        "run_ranker":           tool_run_ranker,
        "run_world_scraper":    tool_run_world_scraper,
        "run_world_ranker":     tool_run_world_ranker,
        "run_summarizer":       tool_run_summarizer,
        "clear_article_links":  tool_clear_article_links,
        "finish":               lambda inp: {"summary": inp.get("summary", "")},
    }

    if tool_name not in dispatch:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    print(f"\n>>> Running tool: {tool_name}")
    try:
        result = dispatch[tool_name](tool_input) if tool_name == "finish" else dispatch[tool_name]()
        return json.dumps(result)
    except Exception as e:
        error = {"error": str(e)}
        print(f"  Tool failed: {e}")
        return json.dumps(error)
# ─────────────────────────────────────────────────────────────
# THE AGENT LOOP
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are the orchestrator for a daily news pipeline. Your job is to
inspect the current state of the database and run exactly the steps
that are needed — no more, no less.

Rules:
1. Always start by calling check_pipeline_state to observe what needs doing.
2. Run reset_tables first, before any scrapers, but only at the start of a fresh daily run.
3. Run scrapers before embedder. Run embedder before clusterer. Run clusterer before ranker.
4. If unfetched_rss_links is 0, skip run_jina_fetcher entirely.
5. If unembedded_articles is 0, skip run_embedder.
6. If unsummarized_articles is 0 after ranker, skip run_summarizer.
7. Always end by calling finish with a summary of what ran and what was skipped.
8. If a tool returns an error, stop and call finish explaining what failed.
"""


def run_agent():
    start = datetime.now(timezone.utc)

    print("\n" + "=" * 55)
    print(f"AI PIPELINE AGENT — {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    # messages is the full conversation history we maintain and send each turn.
    # We start with a single user message kicking things off.
    messages = [
        {
            "role": "user",
            "content": "Run the daily news pipeline. Check the database state first, then decide which steps to run."
        }
    ]

    finished = False

    # The agent loop — runs until Claude calls the finish tool
    while not finished:

        # Send the full conversation to Claude along with the tool list.
        # Claude reads the entire message history to understand what's
        # already been done before deciding what to do next.
        response = client.messages.create(
            model="claude-opus-4-8",   # use Opus — it reasons about tool sequencing better
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        print(f"\n[Claude thinking... stop_reason={response.stop_reason}]")

        # Claude's response is a list of content blocks.
        # Each block is either text (Claude explaining its reasoning)
        # or a tool_use block (Claude saying "call this function").
        tool_results = []

        for block in response.content:

            if block.type == "text":
                # Claude narrating its reasoning — useful for debugging
                print(f"\nClaude: {block.text}")

            elif block.type == "tool_use":
                tool_name  = block.name
                tool_input = block.input   # dict of parameters Claude chose

                print(f"\nClaude chose tool: {tool_name}")
                if tool_input:
                    print(f"  Input: {json.dumps(tool_input)}")

                if tool_name == "finish":
                    # finish is a signal, not a real tool — don't run anything,
                    # just print the summary and exit the loop
                    print(f"\n{'=' * 55}")
                    print("AGENT FINISHED")
                    print(f"  {tool_input.get('summary', '')}")
                    print(f"{'=' * 55}")
                    finished = True

                    # We still need to add the tool result to satisfy the API —
                    # Claude must always get a response to every tool_use block
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     json.dumps({"status": "done"})
                    })

                else:
                    # Run the actual tool and collect the result
                    result_str = run_tool(tool_name, tool_input)

                    # Queue this result to send back to Claude
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,   # must match the id Claude sent
                        "content":     result_str
                    })

        # Add Claude's full response to the conversation history.
        # This is how Claude knows what it already decided.
        messages.append({"role": "assistant", "content": response.content})

        # If there were tool calls, send the results back as a user message.
        # The API requires that tool results come from the "user" role.
        if tool_results and not finished:
            messages.append({
                "role":    "user",
                "content": tool_results
            })

        # Safety valve — if Claude somehow stops without calling finish
        # and there are no tool calls to process, break to avoid infinite loop
        if response.stop_reason == "end_turn" and not tool_results:
            print("\nClaude stopped without calling finish — exiting loop")
            break

    elapsed = (datetime.now(timezone.utc) - start).seconds
    print(f"\nTotal time: {elapsed}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Observe state and plan steps, but don't run anything")
    args = parser.parse_args()

    if args.dry_run:
        DRY_RUN = True
        print("\n*** DRY RUN MODE — no tools will execute, no data will change ***")

    run_agent()