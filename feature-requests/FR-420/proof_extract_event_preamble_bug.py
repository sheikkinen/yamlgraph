"""Standalone proof: extract_event fails when copilot output has preamble.

Run with:
    python feature-requests/FR-420/proof_extract_event_preamble_bug.py

Exits 0 if the bug is confirmed and fix is verified.
Exits 1 if either assertion fails.

Background
----------
The judge copilot node runs successfully (exit 0) but _resolve_event emits
event=error because extract_event returns None.

Hypothesis: the copilot output contains text before the verdict keyword.
The old first-line-only logic fails silently; the all-lines scan would match.

Proof strategy
--------------
1. Embed the OLD first-line-only logic inline — independent of helpers.py state.
2. Test it against realistic copilot output patterns.
3. Show the old logic returns None (bug confirmed).
4. Import the current extract_event from helpers.py and show it returns the event.

The event_map used here is the verbatim value from watcher-pipeline-v2.yaml
after ActionConfig._normalize_event_map lowercases the keys.
"""

from __future__ import annotations

import sys

# ── Verbatim event_map from watcher-pipeline-v2.yaml (post-normalization) ─────
EVENT_MAP: dict[str, str] = {
    "approve": "approve",
    "amend": "revise",
    "reject": "reject",
    "split": "revise",
}


# ── OLD logic: first-line only ─────────────────────────────────────────────────
def _extract_event_old(raw: object, event_map: dict[str, str]) -> str | None:
    """Extract event using the PRE-FIX first-line-only strategy."""
    if isinstance(raw, str):
        candidate = raw.strip().lower()
        mapped = event_map.get(candidate)
        if mapped:
            return mapped
        first_line = candidate.split("\n", 1)[0].strip()
        return event_map.get(first_line)

    d: dict | None = (
        raw
        if isinstance(raw, dict)
        else (raw.model_dump() if hasattr(raw, "model_dump") else None)  # type: ignore[union-attr]
    )
    if d is not None:
        for field_value in d.values():
            if isinstance(field_value, str):
                candidate = field_value.strip().lower()
                mapped = event_map.get(candidate)
                if mapped:
                    return mapped
                first_line = candidate.split("\n", 1)[0].strip()
                mapped = event_map.get(first_line)
                if mapped:
                    return mapped

    return None


# ── Realistic copilot output patterns ─────────────────────────────────────────
# Pattern 1: verdict is the first line — old logic works
CLEAN_OUTPUT = {"output": "APPROVE\n\nThe FR is clear and minimal."}

# Pattern 2: REAL output captured from standalone judge run on 2026-05-19.
# The Copilot CLI prefixes the verdict with its reasoning preamble.
# First line: "Now I have enough context for a thorough judgment. Let me write
# the verdict back into the FR." — NOT a verdict keyword.
# "AMEND" appears on line 3.
REAL_JUDGE_OUTPUT = {
    "output": (
        "Now I have enough context for a thorough judgment. "
        "Let me write the verdict back into the FR.\n\n"
        "AMEND\n\n"
        "**Three issues block APPROVE:**\n\n"
        "1. **AMEND-01 — Integration path is architecturally broken.**..."
    )
}

# Pattern 3: markdown header before verdict (also observed in practice)
HEADER_OUTPUT = {
    "output": (
        "## Judgement\n\n" "APPROVE\n\n" "Reasoning: the FR addresses a single concern."
    )
}

# ── Run proof ──────────────────────────────────────────────────────────────────
OK = "✅"
FAIL = "❌"
failures = 0


def check(label: str, result: object, expected: object) -> None:
    global failures
    status = OK if result == expected else FAIL
    print(f"  {status}  {label}: got={result!r} expected={expected!r}")
    if result != expected:
        failures += 1


print("=== OLD first-line-only logic ===")
check(
    "clean output (first-line verdict)",
    _extract_event_old(CLEAN_OUTPUT, EVENT_MAP),
    "approve",
)
check(
    "real judge output — preamble before AMEND — BUG",
    _extract_event_old(REAL_JUDGE_OUTPUT, EVENT_MAP),
    None,
)
check(
    "markdown header before verdict — BUG",
    _extract_event_old(HEADER_OUTPUT, EVENT_MAP),
    None,
)

print()
print("=== Current extract_event (from helpers.py) ===")
try:
    from yamlgraph.utils.fsm.helpers import extract_event as _extract_event_new
except ImportError as e:
    print(f"  {FAIL}  import failed: {e}")
    sys.exit(1)

check("clean output", _extract_event_new(CLEAN_OUTPUT, EVENT_MAP), "approve")
check(
    "real judge output — AMEND on line 3",
    _extract_event_new(REAL_JUDGE_OUTPUT, EVENT_MAP),
    "revise",
)
check(
    "markdown header before verdict",
    _extract_event_new(HEADER_OUTPUT, EVENT_MAP),
    "approve",
)

print()
# The proof requires:
# - old logic fails on REAL_JUDGE_OUTPUT and HEADER_OUTPUT (confirmed as None)
# - new logic passes all three

old_real_failed = _extract_event_old(REAL_JUDGE_OUTPUT, EVENT_MAP) is None
old_header_failed = _extract_event_old(HEADER_OUTPUT, EVENT_MAP) is None
new_real_ok = _extract_event_new(REAL_JUDGE_OUTPUT, EVENT_MAP) == "revise"
new_header_ok = _extract_event_new(HEADER_OUTPUT, EVENT_MAP) == "approve"

if old_real_failed and old_header_failed:
    print(f"{OK} Bug confirmed: old logic returns None for preamble patterns")
else:
    print(f"{FAIL} Bug NOT confirmed — old logic matched unexpectedly")
    failures += 1

if new_real_ok and new_header_ok:
    print(f"{OK} Fix verified: new logic matches verdict on any line")
else:
    print(f"{FAIL} Fix NOT working — new logic still misses preamble patterns")
    failures += 1

print()
if failures == 0:
    print(f"{OK} All checks passed — bug proved, fix verified")
    sys.exit(0)
else:
    print(f"{FAIL} {failures} check(s) failed")
    sys.exit(1)
