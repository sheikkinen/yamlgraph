"""Source fetching nodes - Hacker News and RSS feeds."""

import logging
from datetime import datetime
from time import struct_time

import feedparser
import httpx

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
RSS_FEEDS = [
    "https://lobste.rs/rss",
    "https://dev.to/feed",
]


def _fetch_hn_story(story_id: int) -> dict | None:
    """Fetch a single HN story by ID."""
    try:
        resp = httpx.get(f"{HN_API_BASE}/item/{story_id}.json", timeout=5)
        data = resp.json()

        if not data or data.get("type") != "story":
            return None

        # Use HN discussion link if no external URL
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
                # Parse published time
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


def fetch_sources(state: dict) -> dict:
    """Fetch from HN and RSS feeds. Limit to 50 total for timeout safety."""
    articles = []
    articles.extend(fetch_hn(limit=30))
    articles.extend(fetch_rss(feeds=RSS_FEEDS, limit=20))

    logger.info(f"📊 Total articles: {len(articles[:50])}")
    return {"raw_articles": articles[:50]}
