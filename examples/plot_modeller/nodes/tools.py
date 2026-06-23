"""FR-570 — Plot Modeller L4 spike: validator + corpus loaders.

The classify LLM node writes raw YAML *text* to ``kinds_raw`` (a non-JSON LLM
node returns the raw response string — ``llm_nodes.py``). ``validate_kinds``
parses that text, checks it, and — only on success — writes the parsed list to
``kinds``. On failure it writes **only** ``validation``, leaving ``kinds``
absent so a later read never sees a raw string where a list is expected (J1).
"""

from __future__ import annotations

from pathlib import Path

import yaml

# The 16-kind Propp-derived alphabet (v5 plan Layer 4).
VALID_KINDS = {
    "villainy",
    "lack",
    "departure",
    "donor_test",
    "provision",
    "struggle",
    "victory",
    "liquidation",
    "return",
    "pursuit",
    "rescue",
    "recognition",
    "exposure",
    "punishment",
    "reconciliation",
    "death",
}


def validate_kinds(state: dict) -> dict:
    """Parse and validate the classify node's raw YAML output (J1).

    Reads ``kinds_raw`` (raw text). On success writes the parsed list to
    ``kinds`` plus ``validation``. On failure writes **only** ``validation``,
    leaving ``kinds`` absent.
    """
    raw = state.get("kinds_raw", "")
    try:
        items = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}

    # yaml.safe_load("") returns None; a scalar is also not a list (J1 crash guard).
    if not isinstance(items, list):
        return {"validation": {"ok": False, "flaws": ["expected a YAML list of items"]}}

    flaws: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            flaws.append(f"non-mapping item: {item!r}")
            continue
        if item.get("kind") not in VALID_KINDS:
            flaws.append(f"{item.get('id', '?')}: unknown kind '{item.get('kind')}'")
        if not item.get("subject"):
            flaws.append(f"{item.get('id', '?')}: missing subject")

    expected = {g["id"] for g in state.get("glosses", [])}
    got = {item.get("id") for item in items if isinstance(item, dict)}
    missing = expected - got
    if missing:
        flaws.append(f"missing: {', '.join(sorted(str(m) for m in missing))}")

    if flaws:
        # J1: do NOT write `kinds` on failure — leave it absent.
        return {"validation": {"ok": False, "flaws": flaws}}

    return {
        "kinds": items,
        "validation": {"ok": True, "flaws": []},
    }


def load_glosses(ground_truth_path: str | Path) -> list[dict]:
    """Extract glosses from a ground-truth plot, stripping kind/subject labels.

    Mode 1 (isolate L4): the model receives only ``id``, ``gloss``, ``chapter``
    and must predict ``kind`` and ``subject`` itself.
    """
    data = yaml.safe_load(Path(ground_truth_path).read_text(encoding="utf-8"))
    glosses: list[dict] = []
    for fn in data.get("functions", []):
        glosses.append(
            {
                "id": fn["id"],
                "gloss": " ".join(str(fn.get("gloss", "")).split()),
                "chapter": fn.get("chapter"),
            }
        )
    return glosses


def load_synopsis(synopsis_path: str | Path) -> str:
    """Read a prose synopsis fixture as plain text."""
    return Path(synopsis_path).read_text(encoding="utf-8")
