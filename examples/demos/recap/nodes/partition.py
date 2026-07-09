"""FR-702: deterministic commit-reference partition (recap demo pre-pass).

Reference detection is arithmetic, not judgement: a commit subject either
contains an FR/NC/issue reference or it does not. Doing this in the model
produced 2/6 orphan false positives in the first field run (mid-subject
refs); doing it here makes that failure class impossible by construction.
"""

from __future__ import annotations

import re

_REF_PATTERN = re.compile(r"(?:FR|NC)-[0-9]+|#[0-9]+", re.IGNORECASE)


def partition_commits(state: dict) -> dict:
    """Split the collected commit lines into referenced / unreferenced.

    Args:
        state: Graph state containing 'commits' (one 'hash|date|subject'
            line per commit, as produced by the commits_since tool).

    Returns:
        State update with 'referenced' and 'unreferenced' newline-joined
        commit lines. Empty input yields two empty strings.
    """
    commits = state.get("commits") or ""
    referenced: list[str] = []
    unreferenced: list[str] = []
    for line in commits.splitlines():
        if not line.strip():
            continue
        bucket = referenced if _REF_PATTERN.search(line) else unreferenced
        bucket.append(line)
    return {
        "referenced": "\n".join(referenced),
        "unreferenced": "\n".join(unreferenced),
    }
