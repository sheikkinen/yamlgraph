#!/usr/bin/env python3
"""Final pre-commit summary hook.

If all hooks pass (we reached this point), print the final summary and the
Distill reminder. Renamed from scripts/absolution.py in FR-439.
"""

import sys


def main() -> int:
    """Print final summary and Distill reminder."""
    print()
    print("✓ Final summary OK")
    print()
    print(
        "**Distill.** After completing a task list, add a metacognitive entry to docs/diary/."
    )
    print("Name the cognitive trap or insight. Extract a heuristic.")
    print("Plant a seed — a forward-looking question to grow new ideas.")
    print("If the heuristic proves recurring, graduate it to the Scripture.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
