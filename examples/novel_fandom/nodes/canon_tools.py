"""Canon lookup and validation tools for worldgen agent (FR-657).

Three tools, three enforcement boundaries:
1. lookup_canon_page — returns full YAML + calendar convention header
2. list_canon_ids — returns all IDs with types
3. validate_draft — mechanical validation of in-progress page

Tools resolve canon_dir from their own location (nodes/ -> ../canon/).
LLM-facing parameters only: id, page_yaml.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CALENDAR_HEADER = (
    "Calendar convention: Year 0 = the Great Flood. "
    "Negative years = before the flood. All birth_years and event years "
    "before the flood must be negative integers."
)

_CANON_DIR = Path(__file__).parent.parent / "canon"


def _load_canon(canon_dir: str | Path | None = None) -> dict[str, dict]:
    """Load all YAML pages from canon directory."""
    canon_path = Path(canon_dir) if canon_dir else _CANON_DIR
    pages: dict[str, dict] = {}
    for f in sorted(canon_path.glob("**/*.yaml")):
        with open(f) as fh:
            page = yaml.safe_load(fh)
        if isinstance(page, dict) and "id" in page:
            pages[page["id"]] = page
    return pages


def lookup_canon_page(id: str, canon_dir: str = "") -> str:
    """Look up a canon entity by ID. Returns full YAML with calendar rules.

    Use this to read any existing character, event, location, or faction
    before generating content that references them.
    """
    pages = _load_canon(canon_dir or None)
    if id not in pages:
        return (
            f"Entity '{id}' not found in canon. "
            "Use list_canon_ids() to see available entities."
        )

    page = pages[id]
    page_yaml = yaml.dump(page, default_flow_style=False, allow_unicode=True)
    return f"{CALENDAR_HEADER}\n\n{page_yaml}"


def list_canon_ids(canon_dir: str = "") -> str:
    """List all entity IDs in the canon with their types.

    Call this first to see what entities exist before generating content.
    """
    pages = _load_canon(canon_dir or None)
    lines = []
    for pid, page in sorted(pages.items()):
        ptype = page.get("type", "unknown")
        lines.append(f"- {pid} ({ptype})")
    return "\n".join(lines)


def validate_draft(page_yaml: str, canon_dir: str = "") -> dict:
    """Validate a draft page before returning it.

    Checks: year sign for events, participant IDs exist, no the_X/X
    duplicate IDs. Returns {"valid": bool, "errors": list[str]}.
    Call this with your generated YAML to catch errors before submitting.
    """
    errors: list[str] = []

    try:
        page = yaml.safe_load(page_yaml)
    except yaml.YAMLError as exc:
        return {"valid": False, "errors": [f"Invalid YAML: {exc}"]}

    if not isinstance(page, dict):
        return {"valid": False, "errors": ["Draft must be a YAML mapping"]}

    pages = _load_canon(canon_dir or None)
    all_ids = set(pages.keys())
    pid = page.get("id", "?")
    ptype = page.get("type", "")

    # Check positive year for events
    if ptype == "event":
        year = page.get("year")
        if year is not None and year > 0:
            errors.append(
                f"{pid}: year {year} is positive — events before the flood "
                f"must have negative years (Year 0 = the Great Flood)"
            )

    # Check participant IDs exist in canon
    for participant in page.get("participants", []):
        if participant not in all_ids:
            errors.append(f"{pid}: participant '{participant}' not found in canon")

    # Check the_X / X duplicate IDs
    if pid.startswith("the_"):
        bare = pid[4:]
        if bare in all_ids:
            errors.append(
                f"{pid}: duplicate of existing '{bare}' " f"(the_ prefix variant)"
            )
    else:
        prefixed = f"the_{pid}"
        if prefixed in all_ids:
            errors.append(
                f"{pid}: duplicate of existing '{prefixed}' " f"(the_ prefix variant)"
            )

    return {"valid": len(errors) == 0, "errors": errors}
