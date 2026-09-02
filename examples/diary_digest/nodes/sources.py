"""Source fetching — HN + RSS feeds for diary digest.

Graph tool functions following the state: dict -> dict pattern.
Copied from daily_digest/nodes/sources.py per judgment correction #5:
own module, own feeds config, no import coupling.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from time import struct_time

import feedparser
import httpx
import yaml

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
FEEDS_PATH = Path(__file__).resolve().parent.parent / "feeds.yaml"
SEEDS_PATH = Path(__file__).resolve().parent.parent / "seeds.yaml"
DIARY_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs"


# ---------------------------------------------------------------------------
# Seed extraction and persistence
# ---------------------------------------------------------------------------

_SEED_RE = re.compile(r"\*\*Seed:\*\*\s*(.+)")


def extract_raw_seeds(diary_dir: Path) -> list[str]:
    """Regex-extract all **Seed:** lines from diary*.md files."""
    seeds: list[str] = []
    for path in sorted(diary_dir.glob("diary*.md")):
        text = path.read_text(encoding="utf-8")
        for match in _SEED_RE.finditer(text):
            seeds.append(match.group(1).strip())
    return seeds


def load_seeds(path: Path) -> list[str]:
    """Read curated seeds from seeds.yaml. Returns [] if missing."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        return []
    return data


def save_seeds(path: Path, seeds: list[str]) -> None:
    """Write curated seed list to seeds.yaml."""
    header = (
        "# Auto-curated by diary-digest pipeline. Do not edit manually.\n"
        f"# Last updated: {datetime.now().strftime('%Y-%m-%d')}\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.dump(seeds, f, default_flow_style=False, allow_unicode=True)


def save_seeds_tool(state: dict) -> dict:
    """Graph tool — write curated seeds to seeds.yaml.

    Reads state.seeds (curated by LLM), writes to file.
    """
    seeds = state.get("seeds", [])
    # Handle Pydantic model or dict
    if hasattr(seeds, "seeds"):
        seeds = seeds.seeds
    if isinstance(seeds, dict):
        seeds = seeds.get("seeds", [])
    save_seeds(SEEDS_PATH, seeds)
    logger.info(f"🌱 Saved {len(seeds)} curated seeds to {SEEDS_PATH}")
    return {"seeds_saved": True}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_feeds_config() -> dict:
    """Load feeds.yaml config file."""
    with open(FEEDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Low-level fetch functions
# ---------------------------------------------------------------------------


def _fetch_hn_story(story_id: int) -> dict | None:
    """Fetch a single HN story by ID."""
    try:
        resp = httpx.get(f"{HN_API_BASE}/item/{story_id}.json", timeout=5)
        data = resp.json()

        if not data or data.get("type") != "story":
            return None

        url = data.get("url") or f"https://news.ycombinator.com/item?id={story_id}"

        return {
            "title": data.get("title", ""),
            "url": url,
            "source": "HN",
            "timestamp": datetime.fromtimestamp(data.get("time", 0)).isoformat(),
        }
    except Exception as e:
        logger.warning(f"Failed to fetch HN story {story_id}: {e}")
        return None


def fetch_hn(limit: int = 30) -> list[dict]:
    """Fetch top stories from Hacker News."""
    try:
        resp = httpx.get(f"{HN_API_BASE}/topstories.json", timeout=10)
        story_ids = resp.json()[:limit]

        stories = []
        for story_id in story_ids:
            story = _fetch_hn_story(story_id)
            if story:
                stories.append(story)

        logger.info(f"📰 Fetched {len(stories)} stories from HN")
        return stories
    except Exception as e:
        logger.error(f"Failed to fetch HN top stories: {e}")
        return []


def fetch_rss(feeds: list[str], limit: int = 20) -> list[dict]:
    """Fetch articles from RSS feeds."""
    articles = []

    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)

            for entry in parsed.entries[:limit]:
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    ts: struct_time = entry.published_parsed
                    timestamp = datetime(*ts[:6]).isoformat()
                else:
                    timestamp = datetime.now().isoformat()

                articles.append(
                    {
                        "title": entry.title,
                        "url": entry.link,
                        "source": "RSS",
                        "timestamp": timestamp,
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to parse RSS feed {feed_url}: {e}")

    logger.info(f"📡 Fetched {len(articles)} articles from RSS")
    return articles[:limit]


def fetch_all_sources(
    feeds: list[str],
    hn_limit: int = 30,
    rss_limit: int = 20,
) -> list[dict]:
    """Fetch combined HN + RSS articles."""
    articles = []
    articles.extend(fetch_hn(limit=hn_limit))
    articles.extend(fetch_rss(feeds=feeds, limit=rss_limit))
    logger.info(f"📊 Total articles: {len(articles)}")
    return articles


# ---------------------------------------------------------------------------
# Graph tool: load_config (state -> dict)
# ---------------------------------------------------------------------------


def load_config(state: dict) -> dict:
    """Load feeds.yaml, seeds.yaml, and diary seeds into state.

    Graph tool — reads config + curated seeds + raw seeds from diary files.
    """
    config = load_feeds_config()
    return {
        "topics": config.get("topics", []),
        "feeds": config.get("feeds", []),
        "seeds": load_seeds(SEEDS_PATH),
        "raw_seeds": extract_raw_seeds(DIARY_DIR),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------------------
# Graph tool: fetch_sources (state -> dict)
# ---------------------------------------------------------------------------


def fetch_sources(state: dict) -> dict:
    """Fetch HN + RSS articles using feeds from state.

    Graph tool — reads state.feeds, returns {raw_articles: [...]}.
    """
    feeds = state.get("feeds", [])
    articles = fetch_all_sources(feeds=feeds, hn_limit=30, rss_limit=20)
    return {"raw_articles": articles}
