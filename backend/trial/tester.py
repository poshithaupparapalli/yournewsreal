import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_vector(text):
    return model.encode(text)

def similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# User who cares about BOTH Lakers AND AI
user = get_vector("Lakers NBA basketball AI technology chips")

articles = [
    # Pure AI
    "NVIDIA reports record quarterly earnings on AI chip demand",
    "OpenAI releases new reasoning model GPT-5",
    
    # Pure sports
    "Lakers beat Celtics in overtime thriller",
    "LeBron James announces retirement from NBA",
    
    # INTERDISCIPLINARY — AI + sports
    "NBA teams are now using AI to predict player injuries",
    "How machine learning is changing how the Lakers draft players",
    
    # INTERDISCIPLINARY — finance + sports
    "Fed rate hikes are forcing NBA teams to cut player salaries",
    "Lakers owner worth drops $2B after stock market crash",
    
    # Totally unrelated
    "Taylor Swift announces new world tour dates",
    "Best pasta recipes for dinner tonight",
]

scores = []
for article in articles:
    vec = get_vector(article)
    score = similarity(user, vec)
    scores.append((score, article))

scores.sort(reverse=True)

print(f"\nUser interests: Lakers + AI\n")
print(f"{'SCORE':<8} ARTICLE")
print("-" * 70)
for score, article in scores:
    print(f"{score:.3f}    {article}")