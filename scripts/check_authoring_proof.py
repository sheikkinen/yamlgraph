#!/usr/bin/env python3
"""FR-767 commit backstop: staged NEW governed graph artifacts must be
listed in tmp/draft-authoring-report.md (the authoring adapter's proof).

Local-only defense-in-depth behind the PreToolUse authoring guard —
this is NOT a CI gate (tmp/ is ignored and absent in CI; C-6).

Governed paths: examples/**/graph.yaml, examples/**/prompts/*.yaml,
graphs/*.yaml (flat), graphs/<name>/*.yaml and graphs/<name>/prompts/*.yaml
(dir-style, FR-1014), .chaplain/graphs/*.yaml. Only newly added (diff-filter=A)
staged files are checked; edits to tracked artifacts are the PreToolUse
guard's concern at write time, not the commit's.
"""

import re
import subprocess
import sys
from pathlib import Path

REPORT = Path("tmp/draft-authoring-report.md")

GOVERNED = (
    re.compile(r"^examples/.+/graph\.ya?ml$"),
    re.compile(r"^examples/.+/prompts/[^/]+\.ya?ml$"),
    re.compile(r"^graphs/[^/]+/[^/]+\.ya?ml$"),
    re.compile(r"^graphs/[^/]+/prompts/[^/]+\.ya?ml$"),
    re.compile(r"^graphs/[^/]+\.ya?ml$"),
    re.compile(r"^\.chaplain/graphs/[^/]+\.ya?ml$"),
)


def staged_new_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    governed_new = [p for p in staged_new_files() if any(g.match(p) for g in GOVERNED)]
    if not governed_new:
        return 0

    report_text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    missing = [p for p in governed_new if p not in report_text]
    if not missing:
        return 0

    print("FR-767 authoring proof missing for new governed graph artifacts:")
    for p in missing:
        print(f"  - {p}")
    print(
        "\nNew governed artifacts must be authored via the sole route\n"
        "(scripts/author.sh <task-brief.md>), which writes\n"
        "tmp/draft-authoring-report.md listing every authored path.\n"
        "Author through the adapter, then commit with the report present."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
