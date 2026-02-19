#!/usr/bin/env python3
"""Run diary-digest pipeline — FR-046.

Fetches HN + RSS, scores relevance, synthesizes a diary entry,
and appends it to docs/diary.md.

Usage:
    python scripts/diary_digest.py                  # write to diary
    python scripts/diary_digest.py --dry-run        # print only
    python scripts/diary_digest.py --commit         # write + git commit
"""

import argparse
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path

# Ensure project root is on sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.diary_digest_tools import (  # noqa: E402
    append_to_diary,
    fetch_all_sources,
    format_diary_entry,
    load_feeds_config,
    should_write_entry,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DIARY_PATH = PROJECT_ROOT / "docs" / "diary.md"


def run_digest(dry_run: bool = False, commit: bool = False) -> None:
    """Execute the diary-digest pipeline."""
    config = load_feeds_config()
    today = date.today().isoformat()

    # 1. Fetch sources
    logger.info("📡 Fetching sources...")
    articles = fetch_all_sources(
        feeds=config["feeds"],
        hn_limit=30,
        rss_limit=20,
    )
    logger.info(f"📊 Fetched {len(articles)} total articles")

    if not articles:
        logger.info("📭 No articles fetched. Nothing to do.")
        return

    # 2. Score relevance via LLM (map node)
    logger.info("🔍 Scoring relevance...")
    try:
        from yamlgraph.executor import execute_prompt

        scored = []
        for article in articles:
            try:
                result = execute_prompt(
                    prompt_path=str(
                        PROJECT_ROOT
                        / "examples"
                        / "diary_digest"
                        / "prompts"
                        / "analyze_relevance.yaml"
                    ),
                    variables={
                        "title": article["title"],
                        "source": article["source"],
                        "topics": config["topics"],
                    },
                )
                article["relevance_score"] = getattr(result, "relevance_score", 0.0)
                article["reason"] = getattr(result, "reason", "")
                scored.append(article)
            except Exception as e:
                logger.warning(f"  ⚠ Failed to score '{article['title']}': {e}")
                article["relevance_score"] = 0.0
                scored.append(article)
    except ImportError:
        logger.warning("⚠ yamlgraph not available — skipping LLM scoring")
        scored = articles
        for a in scored:
            a["relevance_score"] = 0.0

    # 3. Filter to relevant articles
    if not should_write_entry(scored, threshold=0.5):
        logger.info("📭 No relevant developments today. Silent no-op.")
        return

    relevant = [a for a in scored if a.get("relevance_score", 0) >= 0.5]
    logger.info(f"✓ {len(relevant)} articles above relevance threshold")

    # 4. Synthesize diary entry via LLM
    logger.info("📝 Synthesizing diary entry...")
    seeds = config.get("seeds", [])
    try:
        result = execute_prompt(
            prompt_path=str(
                PROJECT_ROOT
                / "examples"
                / "diary_digest"
                / "prompts"
                / "synthesize_diary_entry.yaml"
            ),
            variables={
                "date": today,
                "seeds": seeds,
                "articles": [
                    {
                        "title": a["title"],
                        "url": a["url"],
                        "source": a["source"],
                        "relevance_score": a["relevance_score"],
                        "reason": a.get("reason", ""),
                    }
                    for a in relevant
                ],
            },
        )
        theme = getattr(result, "theme", "Developments")
        body = getattr(result, "body", "No content generated.")
        seed = getattr(result, "seed", "What did we miss?")
    except Exception as e:
        logger.error(f"✗ Failed to synthesize entry: {e}")
        return

    # 5. Format and write
    entry = format_diary_entry(
        date_str=today,
        theme=theme,
        body=body,
        seed=seed,
    )

    if dry_run:
        print("\n--- DRY RUN ---")
        print(entry)
        print("--- END DRY RUN ---\n")
        return

    append_to_diary(DIARY_PATH, entry)
    logger.info(f"✓ Entry appended to {DIARY_PATH}")

    if commit:
        subprocess.run(
            ["git", "add", str(DIARY_PATH)],
            cwd=PROJECT_ROOT,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"docs(diary): World Digest — {today}",
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )
        logger.info("✓ Committed diary entry")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Diary digest — fetch world developments, write diary entry"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print entry to stdout without writing to diary",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Stage and commit the diary entry after writing",
    )
    args = parser.parse_args()

    run_digest(dry_run=args.dry_run, commit=args.commit)


if __name__ == "__main__":
    main()
