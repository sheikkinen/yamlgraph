"""Filter and dedup nodes with SQLite persistence."""

import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_db_path() -> Path:
    """Get database path from environment or default."""
    return Path(os.environ.get("DATABASE_PATH", "digest.db"))


def _get_db() -> sqlite3.Connection:
    """Get SQLite connection, creating table if needed."""
    conn = sqlite3.connect(_get_db_path())
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_urls (
            url TEXT PRIMARY KEY,
            first_seen TEXT
        )
    """)
    return conn


def filter_recent(state: dict, hours: int = 24) -> dict:
    """Filter to last N hours, dedupe by URL across runs."""
    cutoff = datetime.now() - timedelta(hours=hours)
    raw_articles = state.get("raw_articles", [])

    # Filter by time
    recent = []
    for article in raw_articles:
        try:
            ts = datetime.fromisoformat(article["timestamp"])
            if ts > cutoff:
                recent.append(article)
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid timestamp in article: {e}")
            continue

    # Dedupe within batch (by URL)
    by_url = {a["url"]: a for a in recent}

    # Exclude already-seen URLs from previous runs
    conn = _get_db()
    cursor = conn.execute("SELECT url FROM seen_urls")
    seen = {row[0] for row in cursor}

    new_articles = [a for a in by_url.values() if a["url"] not in seen]

    # Mark as seen
    now = datetime.now().isoformat()
    conn.executemany(
        "INSERT OR IGNORE INTO seen_urls (url, first_seen) VALUES (?, ?)",
        [(a["url"], now) for a in new_articles],
    )

    # Cleanup old entries (>30 days)
    conn.execute("DELETE FROM seen_urls WHERE first_seen < date('now', '-30 days')")

    conn.commit()
    conn.close()

    logger.info(f"🔍 Filtered to {len(new_articles)} new articles")
    return {"filtered_articles": new_articles}
