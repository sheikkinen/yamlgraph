"""Compute FR-508 A5 witness metrics from generation log and story artifact.

Run:
  PYTHONPATH="$PWD" .venv/bin/python \
    examples/dungeon_master/scripts/witness_continuity_metrics.py \
    --log logs/gen-10010-azure.log \
    --story outputs/dungeon-master/10010-BC/story/story.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from examples.dungeon_master.api import witness_metrics


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="Path to generation log file")
    ap.add_argument("--story", required=True, help="Path to story.json artifact")
    ap.add_argument(
        "--json",
        action="store_true",
        help="Print JSON summary instead of markdown table",
    )
    args = ap.parse_args()

    log_path = Path(args.log)
    story_path = Path(args.story)

    summary = witness_metrics.build_witness_summary(
        _read_text(log_path), _read_json(story_path)
    )
    if args.json:
        print(witness_metrics.render_json(summary))
    else:
        print(witness_metrics.render_markdown_table(summary))


if __name__ == "__main__":
    main()
