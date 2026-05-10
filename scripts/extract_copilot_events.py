#!/usr/bin/env python3
"""CLI wrapper for Copilot instrumentation event extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from extract_copilot_events_lib import extract_events, render_conformance_table


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract normalized process-mining events from Copilot instrumentation artifacts"
    )
    parser.add_argument(
        "run_dir", help="Path to outputs/copilot-instrumentation/<run-id>"
    )
    parser.add_argument(
        "--conformance-table",
        action="store_true",
        help="Print deterministic per-phase conformance table instead of JSONL events",
    )
    args = parser.parse_args()

    try:
        events = extract_events(Path(args.run_dir))
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"extract_copilot_events.py: {error}", file=sys.stderr)
        return 1

    if args.conformance_table:
        print(render_conformance_table(events))
        return 0

    for event in events:
        print(json.dumps(event.model_dump()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
