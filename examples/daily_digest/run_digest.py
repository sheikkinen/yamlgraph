#!/usr/bin/env python3
"""Run daily digest pipeline locally.

Usage:
    python examples/daily_digest/run_digest.py
    python examples/daily_digest/run_digest.py --dry-run  # No email
    python examples/daily_digest/run_digest.py --topics "AI,Rust"
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

# Add the digest directory to path for local imports (nodes.sources, etc.)
DIGEST_DIR = Path(__file__).parent.resolve()
if str(DIGEST_DIR) not in sys.path:
    sys.path.insert(0, str(DIGEST_DIR))

# Load .env file before any other imports that read env vars
from dotenv import load_dotenv  # noqa: E402

load_dotenv()


def main():
    """Run the daily digest pipeline."""
    parser = argparse.ArgumentParser(description="Run daily digest locally")
    parser.add_argument(
        "--topics",
        default="AI,Python,LangGraph",
        help="Comma-separated topics",
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("RECIPIENT_EMAIL", ""),
        help="Recipient email (or set RECIPIENT_EMAIL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip sending email, print HTML to stdout",
    )
    parser.add_argument(
        "--db",
        default="digest.db",
        help="SQLite database path for dedup",
    )
    args = parser.parse_args()

    # Set database path
    os.environ["DATABASE_PATH"] = args.db

    # Import after env setup
    from yamlgraph.graph_loader import load_and_compile

    # Load graph
    graph_path = Path(__file__).parent / "graph.yaml"
    graph = load_and_compile(str(graph_path))
    compiled = graph.compile()

    # Run
    topics = [t.strip() for t in args.topics.split(",")]
    result = compiled.invoke(
        {
            "topics": topics,
            "recipient_email": args.email if not args.dry_run else "",
            "today": date.today().isoformat(),
            "_dry_run": args.dry_run,
        }
    )

    # Output
    print(f"\n✓ Found {len(result.get('raw_articles', []))} articles")
    print(f"✓ After filtering: {len(result.get('filtered_articles', []))}")

    # Handle Pydantic model for ranked_stories
    ranked = result.get("ranked_stories", [])
    if hasattr(ranked, "stories"):
        ranked = ranked.stories
    print(f"✓ Ranked stories: {len(ranked)}")

    if args.dry_run:
        print("\n--- HTML Output (dry run) ---")
        print(result.get("digest_html", ""))
    else:
        print(f"✓ Email sent: {result.get('email_sent', False)}")


if __name__ == "__main__":
    main()
