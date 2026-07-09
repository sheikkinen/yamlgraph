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


_STATUS_PREFIX = re.compile(r"^\*\*Status:?\*\*:?\s*")


def _parse_status_map(fr_statuses: str) -> dict[str, str]:
    """Parse fr_statuses grep lines into an id→status map.

    Input lines look like (verbatim field format):
    'HEAD:feature-requests/NC-346-offschema-question-stonewall.md:**Status:** ENFORCED ...'
    Duplicate id: first line wins (FR-703 F3).
    """
    status_map: dict[str, str] = {}
    for line in fr_statuses.splitlines():
        if not line.strip():
            continue
        match = _REF_PATTERN.search(line)
        if not match:
            continue
        fr_id = match.group(0).upper()
        # Status text = everything after the last ':**' delimiter of the
        # grep 'path:content' split; strip the markdown **Status:** prefix.
        content = line.split(".md:", 1)[-1]
        status = _STATUS_PREFIX.sub("", content).strip()
        if fr_id not in status_map and status:
            status_map[fr_id] = status
    return status_map


def attach_statuses(state: dict) -> dict:
    """Append verbatim [Status: ...] tags to workstream lines (FR-703).

    The id→status join is arithmetic and must not be a model judgement:
    the FR-702 field run proved the model silently drops joins at ~50
    status lines, and its fallback tag read as verified absence.

    Join semantics (frozen by FR-703 judgement):
    - line names no FR/NC id            → untouched
    - all named ids share one status    → single '[Status: <s>]'
    - statuses differ / partially known → per-id tags '[Status: NC-1 X; NC-2 Y]'
    - no named id resolves              → '[no FR status]'
    """
    recap = state.get("recap") or {}
    if hasattr(recap, "model_dump"):  # normalize at the boundary (F2)
        recap = recap.model_dump()
    status_map = _parse_status_map(state.get("fr_statuses") or "")

    tagged: list[str] = []
    for line in recap.get("workstreams") or []:
        ids = list(
            dict.fromkeys(m.group(0).upper() for m in _REF_PATTERN.finditer(line))
        )
        ids = [i for i in ids if not i.startswith("#")]
        if not ids:
            tagged.append(line)
            continue
        known = {i: status_map[i] for i in ids if i in status_map}
        if not known:
            tagged.append(f"{line} [no FR status]")
        elif len(set(known.values())) == 1 and len(known) == len(ids):
            tagged.append(f"{line} [Status: {next(iter(known.values()))}]")
        else:
            parts = "; ".join(f"{i} {known.get(i, 'no FR status')}" for i in ids)
            tagged.append(f"{line} [Status: {parts}]")

    recap = {**recap, "workstreams": tagged}
    return {"recap": recap}


def _is_graph_prompt_path(path: str) -> bool:
    """Same heuristic the prompt template uses for file-kind partitioning."""
    return path.endswith(".yaml") and ("graphs/" in path or "prompts/" in path)


def _convention_orphans(churn: str, fragments: str) -> list[str]:
    """Window rule (FR-704 J3): graph/prompt churn + zero fragments → flagged.

    Per-FR fragment↔file matching is out of scope; the window-level rule
    catches the real case — a prompt/graph tweak shipped with no fragment
    at all.
    """
    if fragments.strip():
        return []
    seen: dict[str, None] = {}
    for line in churn.splitlines():
        if "\t" not in line:
            continue
        path = line.split("\t")[-1].strip()
        if path and _is_graph_prompt_path(path):
            seen.setdefault(path, None)
    return [f"{path} (no changelog fragment in window)" for path in seen]


def finalize_recap(state: dict) -> dict:
    """Post-pass composing the FR-703 status join with code-owned orphans.

    Orphans never transit the model (FR-704): two field runs proved the
    model corrupts hashes in copy-verbatim steps (703b72d → 703b72e, twice).
    Commit orphans are the unreferenced lines bit-exact, in order; window-rule
    convention entries are appended after (J2).
    """
    result = attach_statuses(state)
    recap = result["recap"]

    unreferenced = state.get("unreferenced") or ""
    orphans = [line for line in unreferenced.splitlines() if line.strip()]
    orphans += _convention_orphans(
        state.get("churn") or "", state.get("fragments") or ""
    )

    return {"recap": {**recap, "orphans": orphans}}
