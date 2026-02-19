"""Diary digest tools — FR-046.

Functions for fetching sources (HN + RSS), formatting diary entries,
and appending them to docs/diary.md. Copied from daily_digest/nodes/sources.py
per judgment: own module, own feeds config, no import coupling.
"""

import logging
from datetime import datetime
from pathlib import Path
from time import struct_time

import feedparser
import httpx
import yaml

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
FEEDS_PATH = Path(__file__).resolve().parent.parent / "feeds.yaml"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_feeds_config() -> dict:
    """Load feeds.yaml config file."""
    with open(FEEDS_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Source fetching (copied from daily_digest, per judgment correction #5)
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
# Diary entry formatting
# ---------------------------------------------------------------------------


def format_diary_entry(
    date_str: str,
    theme: str,
    body: str,
    seed: str,
) -> str:
    """Format a diary entry in the canonical format.

    Returns markdown like:
        \\n---\\n\\n## 2026-02-19: World Digest — Theme\\n\\nbody\\n\\n**Seed:** ...\\n
    """
    return (
        f"\n---\n\n## {date_str}: World Digest — {theme}\n\n"
        f"{body}\n\n"
        f"**Seed:** {seed}\n"
    )


def append_to_diary(path: Path, entry: str) -> None:
    """Append a formatted entry to the diary file."""
    with open(path, "a") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# No-op behavior (judgment correction #6)
# ---------------------------------------------------------------------------


def should_write_entry(
    articles: list[dict],
    threshold: float = 0.7,
) -> bool:
    """Return True only if at least one article scores above threshold.

    When no articles are relevant, the digest should be a silent no-op.
    """
    if not articles:
        return False
    return any(a.get("relevance_score", 0) >= threshold for a in articles)
