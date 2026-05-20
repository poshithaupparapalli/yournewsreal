"""
visualize_interactive.py
─────────────────────────
Shows articles colored by cluster, users as stars, and lines to their
actual briefing articles (from the briefings table).

Hover article → title, source, cluster, LLM summary
Hover user star → interests + their briefing articles

Improvements:
- Each user gets their own line color so you can see whose briefing is whose
- Interest lines are solid, learning lines are dashed
- Briefing articles get a glowing ring so they stand out from background articles
- Cluster legend hidden (50 entries = unreadable) — colors still visible on dots
- Cluster centroids labeled with cluster number
- Larger dots and cleaner layout
"""

import os, sys, ast
import numpy as np
import plotly.graph_objects as go
from sklearn.decomposition import PCA
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import supabase
from dotenv import load_dotenv
load_dotenv()

def parse_vec(v):
    if v is None: return None
    if isinstance(v, str): v = ast.literal_eval(v)
    return np.array(v, dtype=float)

def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Converts a #rrggbb hex color to rgba(r,g,b,alpha) for Plotly."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

print("Fetching articles...")
articles_raw = (
    supabase.table("articles")
    .select("id, title, source, cluster_id, embedding, llm_summary, url")
    .not_.is_("embedding", "null")
    .not_.is_("cluster_id", "null")
    .execute()
).data

print("Fetching users...")
users_raw = (
    supabase.table("users_waitlist")
    .select("id, name, email, interests_raw, interests_raw_vector")
    .not_.is_("interests_raw_vector", "null")
    .execute()
).data

print("Fetching today's briefings...")
today = datetime.now(timezone.utc).date().isoformat()
briefings_raw = (
    supabase.table("briefings")
    .select("user_id, interest_article_ids, learning_article_ids")
    .eq("date", today)
    .execute()
).data

articles = [a for a in articles_raw if parse_vec(a["embedding"]) is not None]
users    = [u for u in users_raw    if parse_vec(u["interests_raw_vector"]) is not None]
print(f"Articles: {len(articles)} | Users: {len(users)} | Briefings: {len(briefings_raw)}")

# map user_id → {interest_ids, learning_ids}
briefing_map = {}
for b in briefings_raw:
    uid = b["user_id"]
    briefing_map[uid] = {
        "interest": b.get("interest_article_ids") or [],
        "learning": b.get("learning_article_ids") or [],
    }

# set of all article ids that appear in any briefing (used to highlight them)
briefed_article_ids = set()
for b in briefing_map.values():
    briefed_article_ids.update(b["interest"])
    briefed_article_ids.update(b["learning"])

# map article id → index
article_idx = {a["id"]: i for i, a in enumerate(articles)}

# PCA — fit on articles + users together so they share the same 2D space
article_vecs = np.array([parse_vec(a["embedding"]) for a in articles])
user_vecs    = np.array([parse_vec(u["interests_raw_vector"]) for u in users])
pca    = PCA(n_components=2)
all_2d = pca.fit_transform(np.vstack([article_vecs, user_vecs]))
article_2d = all_2d[:len(articles)]
user_2d    = all_2d[len(articles):]
print(f"PCA variance explained: {pca.explained_variance_ratio_.sum():.1%}")

# one color per cluster (articles)
clusters = sorted(set(a.get("cluster_id", 0) for a in articles))
palette  = [
    "#4e9af1","#f4845f","#63b3a0","#c678dd","#e5c07b","#98c379","#56b6c2",
    "#e06c75","#abb2bf","#d19a66","#61afef","#7fcfb8","#ff79c6","#bd93f9",
    "#50fa7b","#ffb86c","#8be9fd","#ff5555","#f1fa8c","#6272a4","#a4c2f4",
    "#ea6c73","#b5cea8","#dcdcaa","#9cdcfe","#ce9178","#4ec9b0","#c8c8c8",
]
cluster_color = {c: palette[i % len(palette)] for i, c in enumerate(clusters)}

# one color per user (connection lines)
user_line_palette = [
    "#ff6b6b","#4ecdc4","#45b7d1","#96ceb4","#ffeaa7",
    "#dfe6e9","#fd79a8","#a29bfe","#55efc4","#fdcb6e",
    "#e17055","#74b9ff","#00b894","#fab1a0","#81ecec",
    "#636e72","#b2bec3","#2d3436","#6c5ce7","#00cec9",
]
user_color = {u["id"]: user_line_palette[i % len(user_line_palette)] for i, u in enumerate(users)}

fig = go.Figure()

# ── connection lines: user → interest articles (solid) and learning (dashed) ──
for i, user in enumerate(users):
    uid   = user["id"]
    color = user_color[uid]
    name  = (user.get("name") or user.get("email") or "?").split()[0]
    bmap  = briefing_map.get(uid, {"interest": [], "learning": []})

    for aid in bmap["interest"]:
        j = article_idx.get(aid)
        if j is None: continue
        ux, uy = user_2d[i]
        ax, ay = article_2d[j]
        fig.add_trace(go.Scatter(
            x=[ux, ax, None], y=[uy, ay, None],
            mode="lines",
            line=dict(color=hex_to_rgba(color, 0.55), width=1.5),
            hoverinfo="skip", showlegend=False,
        ))

    for aid in bmap["learning"]:
        j = article_idx.get(aid)
        if j is None: continue
        ux, uy = user_2d[i]
        ax, ay = article_2d[j]
        fig.add_trace(go.Scatter(
            x=[ux, ax, None], y=[uy, ay, None],
            mode="lines",
            line=dict(color=hex_to_rgba(color, 0.4), width=1.5, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ))

# ── background articles (not in any briefing) — smaller, dimmer ──
bg_idxs = [i for i, a in enumerate(articles) if a["id"] not in briefed_article_ids]
if bg_idxs:
    fig.add_trace(go.Scatter(
        x=[article_2d[i][0] for i in bg_idxs],
        y=[article_2d[i][1] for i in bg_idxs],
        mode="markers",
        name="articles (not briefed)",
        marker=dict(
            color=[cluster_color[articles[i]["cluster_id"]] for i in bg_idxs],
            size=7, opacity=0.35,
            line=dict(width=0),
        ),
        text=[
            f"<b>{articles[i].get('title') or 'untitled'}</b><br>"
            f"<span style='color:#aaa'>{(articles[i].get('source') or '').replace('_',' ').title()} · cluster {articles[i].get('cluster_id')}</span><br><br>"
            f"{(articles[i].get('llm_summary') or '')[:250]}"
            for i in bg_idxs
        ],
        hovertemplate="%{text}<extra></extra>",
        showlegend=True,
    ))

# ── briefed articles — larger, full opacity, white ring so they pop ──
briefed_idxs = [i for i, a in enumerate(articles) if a["id"] in briefed_article_ids]
if briefed_idxs:
    fig.add_trace(go.Scatter(
        x=[article_2d[i][0] for i in briefed_idxs],
        y=[article_2d[i][1] for i in briefed_idxs],
        mode="markers",
        name="articles (in a briefing)",
        marker=dict(
            color=[cluster_color[articles[i]["cluster_id"]] for i in briefed_idxs],
            size=13, opacity=1.0,
            line=dict(width=2, color="white"),
        ),
        text=[
            f"<b>{articles[i].get('title') or 'untitled'}</b><br>"
            f"<span style='color:#aaa'>{(articles[i].get('source') or '').replace('_',' ').title()} · cluster {articles[i].get('cluster_id')}</span><br><br>"
            f"{(articles[i].get('llm_summary') or '')[:300]}<br><br>"
            f"<a href='{articles[i].get('url') or ''}' style='color:#61afef'>{(articles[i].get('url') or '')[:55]}...</a>"
            for i in briefed_idxs
        ],
        hovertemplate="%{text}<extra></extra>",
        showlegend=True,
    ))

# ── cluster centroid labels ──
for cluster_id in clusters:
    idxs = [i for i, a in enumerate(articles) if a.get("cluster_id") == cluster_id]
    if not idxs: continue
    cx = np.mean([article_2d[i][0] for i in idxs])
    cy = np.mean([article_2d[i][1] for i in idxs])
    fig.add_trace(go.Scatter(
        x=[cx], y=[cy],
        mode="text",
        text=[f"<span style='color:{cluster_color[cluster_id]};font-size:9px;opacity:0.6'>{cluster_id}</span>"],
        textposition="middle center",
        hoverinfo="skip", showlegend=False,
    ))

# ── users — colored stars, hover shows their full briefing ──
user_hover = []
for i, user in enumerate(users):
    name      = user.get("name") or user.get("email") or "?"
    interests = (user.get("interests_raw") or "")[:200]
    uid       = user["id"]
    bmap      = briefing_map.get(uid, {"interest": [], "learning": []})
    color     = user_color[uid]

    interest_lines = ""
    for aid in bmap["interest"]:
        j = article_idx.get(aid)
        if j is None: continue
        interest_lines += f"  · {(articles[j].get('title') or '')[:65]}<br>"

    learning_lines = ""
    for aid in bmap["learning"]:
        j = article_idx.get(aid)
        if j is None: continue
        learning_lines += f"  · {(articles[j].get('title') or '')[:65]}<br>"

    total = len(bmap["interest"]) + len(bmap["learning"])
    user_hover.append(
        f"<b style='color:{color}'>★ {name}</b><br><br>"
        f"<b>interests:</b><br>{interests}<br><br>"
        f"<b>interest picks ({len(bmap['interest'])}):</b><br>{interest_lines or 'none'}<br>"
        f"<b>learning pick ({len(bmap['learning'])}):</b><br>{learning_lines or 'none'}"
    )

fig.add_trace(go.Scatter(
    x=user_2d[:, 0], y=user_2d[:, 1],
    mode="markers+text",
    name="users",
    marker=dict(
        symbol="star",
        color=[user_color[u["id"]] for u in users],
        size=22,
        line=dict(width=1.5, color="white"),
    ),
    text=[(u.get("name") or u.get("email") or "?").split()[0] for u in users],
    textposition="top right",
    textfont=dict(color="white", size=11),
    hovertext=user_hover,
    hovertemplate="%{hovertext}<extra></extra>",
))

# ── legend for user line colors ──
for i, user in enumerate(users):
    name  = (user.get("name") or user.get("email") or "?").split()[0]
    color = user_color[user["id"]]
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="lines",
        name=f"{name} (solid=interest · dot=learning)",
        line=dict(color=color, width=2),
        showlegend=True,
    ))

fig.update_layout(
    title=dict(
        text="resonance — article clusters · briefed articles (large+ring) · user stars (colored by user)",
        font=dict(color="white", size=14), x=0.5,
    ),
    paper_bgcolor="#0d0d0d", plot_bgcolor="#111111",
    font=dict(color="#ccc"),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    legend=dict(
        bgcolor="rgba(15,15,15,0.9)", bordercolor="#333", borderwidth=1,
        font=dict(size=10), x=1.01, y=1, xanchor="left",
    ),
    hovermode="closest",
    hoverlabel=dict(
        bgcolor="#1a1a2e", bordercolor="#555",
        font=dict(color="white", size=12), align="left",
        namelength=0,
    ),
    width=1500, height=950,
    margin=dict(l=20, r=260, t=70, b=20),
)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "embedding_map.html")
fig.write_html(out, include_plotlyjs="cdn")
print(f"\nSaved → {out}")

import subprocess
subprocess.run(["open", out])
