"""Census brief: citation-checked human-readable tail (FR-895).

The synthesis LLM emits structured claim blocks; this LLM-free boundary
validates every citation against the source artifact BEFORE rendering
(R-1). Fail-closed emission (R-2): rejection produces no brief — only a
.REJECTED.md failure artifact carrying the deterministic summary head and
reasons. Synthesis input is bounded and column-allowlisted (R-4/R-5).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ALLOWED_INPUT_COLUMNS = (
    "label",
    "entries",
    "citations",
    "first_seen",
    "last_seen",
    "item_ref",
    "judgement",
    "confidence",
)
DEFAULT_MAX_ROWS = 60
SUMMARY_HEAD_ROWS = 10


def build_synthesis_input(
    rows: list[dict[str, Any]], *, max_rows: int = DEFAULT_MAX_ROWS
) -> list[dict[str, Any]]:
    """Bounded, public-safe synthesis input: top-N by weight, allowlisted."""

    def weight(row: dict[str, Any]) -> int:
        return int(row.get("entries", 1) or 1)

    selected = sorted(rows, key=weight, reverse=True)[:max_rows]
    return [
        {k: v for k, v in row.items() if k in ALLOWED_INPUT_COLUMNS} for row in selected
    ]


def _known_ids(rows: list[dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        if row.get("label"):
            ids.add(f"label:{row['label']}")
        if row.get("item_ref"):
            ids.add(f"row:{row['item_ref']}")
    return ids


def validate_claims(
    claims: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> list[str]:
    """Mechanical citation checks; returns error list (empty = accepted)."""
    known = _known_ids(rows)
    errors: list[str] = []
    for i, claim in enumerate(claims):
        cid = str(claim.get("claim_id") or f"<claim {i}>")
        text = str(claim.get("text") or "").strip()
        citations = claim.get("citations") or []
        if not text:
            errors.append(f"{cid}: empty claim text")
        if not isinstance(citations, list) or not citations:
            errors.append(f"{cid}: claim has no citations")
            continue
        for cite in citations:
            if str(cite) not in known:
                errors.append(f"{cid}: citation not in source artifact: {cite}")
    if not claims:
        errors.append("no claims emitted")
    return errors


def _summary_head(rows: list[dict[str, Any]]) -> list[str]:
    top = build_synthesis_input(rows, max_rows=SUMMARY_HEAD_ROWS)
    lines = ["## Summary head (deterministic, code-generated)", ""]
    for row in top:
        ident = row.get("label") or row.get("item_ref", "?")
        count = row.get("entries", row.get("confidence", ""))
        lines.append(f"- {ident} ({count})")
    lines.append("")
    return lines


def emit_brief(
    claims: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    brief_path: str,
    *,
    run_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate claims and emit the brief, or the .REJECTED.md artifact."""
    path = Path(brief_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    errors = validate_claims(claims, rows)
    meta_lines = [f"- {k}: {v}" for k, v in (run_meta or {}).items()]

    if errors:
        rejected = path.with_name(path.stem + ".REJECTED.md")
        lines = (
            ["# Census brief REJECTED (citation boundary)", ""]
            + _summary_head(rows)
            + ["## Rejection reasons", ""]
            + [f"- {e}" for e in errors]
            + [""]
            + meta_lines
        )
        rejected.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"accepted": False, "errors": errors, "artifact": str(rejected)}

    lines = ["# Census Brief", ""] + _summary_head(rows) + ["## Findings", ""]
    for claim in claims:
        cites = ", ".join(str(c) for c in claim.get("citations", []))
        conf = claim.get("confidence")
        conf_txt = f" (confidence {conf})" if conf is not None else ""
        lines.append(f"- {claim['text']}{conf_txt} [{cites}]")
    lines += ["", "## Run provenance", ""] + meta_lines
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"accepted": True, "errors": [], "artifact": str(path)}
