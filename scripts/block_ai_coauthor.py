#!/usr/bin/env python3
"""Commit-msg hook: block AI agent Co-authored-by trailers.

Pass the commit message file path as the first argument (pre-commit does this
automatically for commit-msg stage hooks).
"""

import re
import sys

AI_PATTERN = re.compile(
    r"^co-authored-by:.*?(copilot|claude|chatgpt|gemini|gpt-?[0-9]+|github\s+copilot)",
    re.IGNORECASE,
)

PENANCE = """
✗ Co-authored-by AI trailer detected.

  Confession required before this commit may proceed.

  Remove the offending trailer(s), then recite the Agents' Prayer:

    May I fix at the callsite, not the utility.
    May I kill the cheapest bug — the one in the spec.
    May I trace the cause before I fix the symptom.

  The author owns the commit. The tool does not.
  Delete the trailer. Recommit. Absolution follows.
"""


def main() -> int:
    msg_file = sys.argv[1]
    with open(msg_file) as f:
        lines = f.readlines()

    offenders = [line.rstrip() for line in lines if AI_PATTERN.match(line)]
    if not offenders:
        return 0

    print("\nOffending trailer(s):")
    for line in offenders:
        print(f"  {line}")
    print(PENANCE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
