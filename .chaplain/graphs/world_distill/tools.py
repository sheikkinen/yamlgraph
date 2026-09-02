"""FR-744: world_distill tools — fetch, cap, write. REQ-YG-563.

Commandment 6 at both boundaries: zero fetch yield raises; an empty
distill result refuses to overwrite the world. Per-feed failures are
tolerated (a dead feed is weather); total silence is an error.
"""

from __future__ import annotations

import logging
from datetime import date as _date

import httpx

logger = logging.getLogger(__name__)

try:
    import feedparser
except ImportError as e:  # the daily_digest DOA exhibit: name the missing dep
    raise ImportError(
        "world_distill requires 'feedparser' (pip install feedparser)"
    ) from e

EXCERPT_CAP = 500  # F3: title + source + excerpt, never full content
HN_API = "https://hacker-news.firebaseio.com/v0"

# F2: curated ecosystem feeds — editorial config, not general tech news.
# The March exemplar's bar: LangGraph releases, agent observability,
# evaluation pipelines. Adjust freely; the raw read judges fitness.
DEFAULT_FEEDS = [
    "https://blog.langchain.com/rss/",
    "https://simonwillison.net/atom/everything/",
    "https://huggingface.co/blog/feed.xml",
]
HN_KEYWORDS = (
    "llm",
    "agent",
    "langgraph",
    "langchain",
    "anthropic",
    "openai",
    "claude",
    "gpt",
    "prompt",
    "rag",
    "evaluation",
    "mcp",
)


def fetch_ecosystem(state: dict) -> dict:
    """Curated feeds + keyword-filtered HN front page. Per-feed failure
    tolerated; zero TOTAL yield raises (Commandment 6)."""
    feeds = state.get("feeds") or DEFAULT_FEEDS
    articles: list[dict] = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:10]:
                articles.append(
                    {
                        "title": entry.get("title", ""),
                        "source": url,
                        "content": entry.get("summary", "")[:2000],
                    }
                )
        except Exception as e:  # noqa: BLE001 — a dead feed is weather
            logger.warning("feed failed (tolerated): %s: %s", url, e)
    try:
        ids = httpx.get(f"{HN_API}/topstories.json", timeout=10).json()[:60]
        for sid in ids:
            item = httpx.get(f"{HN_API}/item/{sid}.json", timeout=5).json() or {}
            title = item.get("title", "")
            if any(k in title.lower() for k in HN_KEYWORDS):
                articles.append(
                    {"title": title, "source": "hn", "content": item.get("url", "")}
                )
    except Exception as e:  # noqa: BLE001
        logger.warning("HN fetch failed (tolerated): %s", e)
    if not articles:
        raise ValueError(
            "zero articles from all sources — refusing to distill an empty world"
        )
    logger.info("📊 ecosystem articles: %d", len(articles))
    return {"articles": articles}


def prepare_distill_input(state: dict) -> dict:
    """F3: cap each article at title + source + 500-char excerpt."""
    articles = state.get("articles") or []
    if not articles:
        raise ValueError("no articles to distill — zero yield is an error")
    blocks = [
        f"- {a.get('title', '')} [{a.get('source', '')}]\n"
        f"  {(a.get('content') or '')[:EXCERPT_CAP]}"
        for a in articles
    ]
    return {"distill_input": "\n".join(blocks)}


def write_context(state: dict) -> dict:
    """Render the dated world-context file (F1: dated header + prose).
    Refuses an empty distill result — never overwrite the world with
    nothing (Commandment 6 at the write boundary)."""
    d = state.get("distilled") or {}
    highlights = d.get("highlights") or []
    themes = d.get("themes") or []
    questions = d.get("open_questions") or []
    if not (highlights or themes):
        raise ValueError("empty distill result — refusing to overwrite world-context")
    today = state.get("date") or _date.today().isoformat()
    lines = [
        "# World Context",
        "",
        f"Last updated: {today}",
        "",
        "## Ecosystem Highlights",
        *[f"- {h}" for h in highlights],
        "",
        "## Emerging Themes",
        *[f"- {t}" for t in themes],
        "",
        "## Open Questions",
        *[f"- {q}" for q in questions],
        "",
    ]
    out = state.get("output_path") or "docs/world-context.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(
        "🌍 wrote %s (%d highlights, %d themes)", out, len(highlights), len(themes)
    )
    return {"written": True}
