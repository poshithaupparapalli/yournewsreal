"""
ranking_tester.py

Tests two approaches to understanding user interests:
  Method A: Embed the raw text directly
  Method B: Pass through LLM first, extract entities, then embed

Run with: python3 ranking_tester.py
Requires: pip3 install sentence-transformers anthropic
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import anthropic
import json

# ─────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────

model = SentenceTransformer('all-MiniLM-L6-v2')
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

# ─────────────────────────────────────────────────────────────
# SIMULATED USER INPUTS
# Test with different types of users to see which method wins
# ─────────────────────────────────────────────────────────────

USERS = [
    {
        "name": "Tech / AI user",
        "interests": """
            I follow Jensen Huang really closely, super interested in what NVIDIA 
            is doing with the Blackwell chips. Also care a lot about AI policy, 
            especially the export controls to China. Sam Altman and what OpenAI 
            is doing is always on my radar. Demis Hassabis too.
        """,
        "learning_goals": "I want to understand how semiconductor supply chains actually work"
    },
    {
        "name": "Finance / markets user",
        "interests": """
            Fed decisions are really important to me, especially how Powell 
            thinks about inflation. I follow hedge funds like Bridgewater, 
            Ray Dalio's writing. Private equity and what's happening with 
            interest rates. Also keeping an eye on what's happening with 
            the dollar and emerging markets.
        """,
        "learning_goals": "I want to understand how central banks actually coordinate globally"
    },
    {
        "name": "Mixed / interdisciplinary user",
        "interests": """
            Climate tech is huge for me, especially battery storage and 
            what Tesla and CATL are doing. But I also follow Formula 1 
            and how the teams use data. Elon Musk across everything — 
            Tesla, SpaceX, xAI. Also geopolitics especially US-China.
        """,
        "learning_goals": "I want to understand how carbon markets actually work"
    }
]

# ─────────────────────────────────────────────────────────────
# SIMULATED ARTICLES
# Mix of relevant and irrelevant to test discrimination
# ─────────────────────────────────────────────────────────────

ARTICLES = [
    # AI / Tech
    "NVIDIA reports record quarterly earnings driven by Blackwell GPU demand from hyperscalers",
    "Jensen Huang keynote at GTC 2025 reveals next generation AI chip roadmap",
    "OpenAI raises $6.6 billion at $157 billion valuation as Sam Altman eyes AGI",
    "Demis Hassabis wins Nobel Prize for AlphaFold protein structure breakthrough",
    "US restricts AI chip exports to China tightening controls on H100 and A100",
    "Anthropic releases Claude 3.5 with improved reasoning and coding capabilities",
    "Google DeepMind announces Gemini Ultra outperforms GPT-4 on key benchmarks",
    
    # Finance / Markets
    "Federal Reserve raises interest rates by 25 basis points as Powell signals pause",
    "Ray Dalio warns of debt crisis as US deficit reaches historic levels",
    "Bridgewater Associates bets on emerging market currencies amid dollar weakness",
    "Private equity firms face rising pressure as interest rates squeeze leveraged buyouts",
    "Bank of Japan surprises markets with rate hike ending decades of negative rates",
    "Inflation data shows core CPI rising 3.2 percent missing Fed target",
    
    # Climate / Energy
    "Tesla Megapack battery storage deployments triple as grid-scale demand surges",
    "CATL unveils sodium-ion battery claiming 500 mile range at lower cost than lithium",
    "Carbon credit market reaches 2 trillion as European firms rush to offset emissions",
    "SpaceX Starship completes first full orbital test flight with successful splashdown",
    "Elon Musk unveils xAI Grok 2 claiming it surpasses GPT-4 on math benchmarks",
    
    # Formula 1
    "Max Verstappen wins Japanese Grand Prix extending championship lead over Hamilton",
    "Ferrari introduces radical new floor design at Spanish Grand Prix",
    "Formula 1 teams debate budget cap increase as costs rise across the grid",
    
    # Geopolitics
    "US-China tensions rise as Taiwan Strait incidents increase in frequency",
    "NATO allies commit to increased defense spending following Russian threats",
    "South China Sea dispute escalates as Philippines files new protest with UN",
    
    # Irrelevant
    "Taylor Swift announces Eras Tour extension adding 50 new concert dates",
    "Lakers beat Celtics in overtime thriller as LeBron James scores 40 points",
    "Best pasta recipes for a quick weeknight dinner under 30 minutes",
    "Royal family announces new baby as King Charles celebrates milestone birthday",
    "Premier League transfer window opens with clubs eyeing record signings",
]

# ─────────────────────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────

def cosine_similarity(a, b):
    """Measure similarity between two vectors. Returns -1 to 1."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def method_a_raw_embed(interests, learning_goals):
    """
    Method A: Embed the raw text directly.
    No processing. Just convert text to vector.
    """
    combined = interests.strip() + " " + learning_goals.strip()
    vector = model.encode(combined)
    return vector, combined


def method_b_llm_extract(interests, learning_goals):
    """
    Method B: Pass through Claude first to extract clean entities.
    Then embed the extracted entities.
    """
    prompt = f"""
You must return ONLY a JSON object. No explanation. No markdown. No backticks.
Just the raw JSON object starting with {{ and ending with }}.

Extract interests from:
Interests: {interests}
Learning goals: {learning_goals}

Return exactly this structure:
{{"people": [], "companies": [], "topics": [], "learning_goals": []}}

Rules:
- Only include things explicitly mentioned
- people = real named individuals
- companies = named organisations
- topics = subject areas or concepts
- Keep each item concise (2-4 words max)
- Return valid JSON only
"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        # if JSON parsing fails, fall back to raw embedding
        print("    ⚠️  LLM returned invalid JSON, falling back to raw text")
        return method_a_raw_embed(interests, learning_goals)

    # Build a clean text from extracted entities
    all_items = (
        extracted.get("people", []) +
        extracted.get("companies", []) +
        extracted.get("topics", []) +
        extracted.get("learning_goals", [])
    )
    clean_text = " ".join(all_items)

    vector = model.encode(clean_text)
    return vector, extracted


def rank_articles(user_vector, articles):
    """Score and rank all articles against the user vector."""
    scores = []
    for article in articles:
        article_vec = model.encode(article)
        score = cosine_similarity(user_vector, article_vec)
        scores.append((score, article))
    scores.sort(reverse=True)
    return scores


def print_results(method_name, extracted_data, ranked, top_n=8):
    """Print ranked results cleanly."""
    print(f"\n  {'─'*60}")
    print(f"  {method_name}")
    print(f"  {'─'*60}")

    if isinstance(extracted_data, dict):
        print(f"  Extracted:")
        for key, values in extracted_data.items():
            if values:
                print(f"    {key}: {', '.join(values)}")
    else:
        words = extracted_data.split()[:12]
        print(f"  Input (first 12 words): {' '.join(words)}...")

    print(f"\n  Top {top_n} ranked articles:")
    for i, (score, article) in enumerate(ranked[:top_n], 1):
        bar = "█" * int(score * 20)
        print(f"  {i:2}. {score:.3f} {bar}")
        print(f"      {article[:75]}...")

    print(f"\n  Bottom 3 (should be irrelevant):")
    for score, article in ranked[-3:]:
        print(f"      {score:.3f}  {article[:75]}...")


def compare_methods(user):
    """Run both methods on one user and compare results."""
    print(f"\n{'═'*70}")
    print(f"USER: {user['name']}")
    print(f"{'═'*70}")
    print(f"Interests: {user['interests'].strip()[:120]}...")
    print(f"Learning:  {user['learning_goals'].strip()}")

    # Method A
    print(f"\n⏳ Running Method A (raw embed)...")
    vec_a, data_a = method_a_raw_embed(user["interests"], user["learning_goals"])
    ranked_a = rank_articles(vec_a, ARTICLES)

    # Method B
    print(f"⏳ Running Method B (LLM extract)...")
    vec_b, data_b = method_b_llm_extract(user["interests"], user["learning_goals"])
    ranked_b = rank_articles(vec_b, ARTICLES)

    # Print both
    print_results("METHOD A — Raw embedding", data_a, ranked_a)
    print_results("METHOD B — LLM extraction", data_b, ranked_b)

    # Compare top 5 overlap
    top5_a = set(a for _, a in ranked_a[:5])
    top5_b = set(a for _, a in ranked_b[:5])
    overlap = top5_a & top5_b
    different = (top5_a - top5_b) | (top5_b - top5_a)

    print(f"\n  COMPARISON:")
    print(f"  Articles in both top 5:  {len(overlap)}/5")
    print(f"  Articles different:      {len(different)}")
    if different:
        print(f"  Differences:")
        for article in different:
            in_a = "A" if article in top5_a else " "
            in_b = "B" if article in top5_b else " "
            print(f"    [{in_a}][{in_b}] {article[:70]}...")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("\n" + "═"*70)
    print("RANKING TESTER — Method A vs Method B")
    print("Method A: embed raw text directly")
    print("Method B: LLM extracts entities first, then embed")
    print("="*70)
    print(f"Testing {len(USERS)} user profiles against {len(ARTICLES)} articles")

    for user in USERS:
        compare_methods(user)

    print(f"\n{'═'*70}")
    print("DONE")
    print("Look at each user's results and ask:")
    print("  1. Did the right articles appear in the top 5?")
    print("  2. Are irrelevant articles (sports, recipes) at the bottom?")
    print("  3. Does Method B find articles Method A missed?")
    print("  4. Is Method B worth the extra API call and latency?")
    print("="*70)


if __name__ == "__main__":
    main()