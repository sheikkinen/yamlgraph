"""Validate deepened + skeleton pages before persist.

Gate checks references against the merged canon (existing pages +
deepened updates + new skeletons from this iteration).
"""

from __future__ import annotations

from typing import Any


def _extract_ref_ids(refs: list) -> list[str]:
    """Extract string ids from references that may be strings or dicts."""
    ids = []
    for ref in refs:
        if isinstance(ref, str):
            ids.append(ref)
        elif isinstance(ref, dict):
            # LLM may return {to: "kaelen"} or {target: "kaelen"} or {id: "kaelen"}
            for key in ("to", "target", "id"):
                if key in ref:
                    ids.append(ref[key])
                    break
    return ids


def validate_pages(state: dict[str, Any]) -> dict[str, Any]:
    """Validate references for deepened and skeleton pages.

    Builds a merged id set: existing canon + deepened updates + skeletons.
    Checks every reference in every new/updated page resolves.
    """
    canon_pages = state.get("canon_pages", {})
    deepened = state.get("deepened", [])
    skeletons = state.get("skeletons", [])

    # Build merged id set: everything that will exist after persist
    merged_ids = set(canon_pages.keys())
    for result in deepened:
        if isinstance(result, dict):
            page = result.get("updated_page", {})
            if isinstance(page, dict) and "id" in page:
                merged_ids.add(page["id"])
    for skel in skeletons:
        if isinstance(skel, dict):
            # May be wrapped in {page: {...}} from schema
            page = skel.get("page", skel) if "page" in skel else skel
            if isinstance(page, dict) and "id" in page:
                merged_ids.add(page["id"])

    violations: list[str] = []

    # Check deepened pages
    for result in deepened:
        if not isinstance(result, dict):
            continue
        page = result.get("updated_page", {})
        if not isinstance(page, dict):
            continue
        pid = page.get("id", "?")
        for ref in _extract_ref_ids(page.get("references", [])):
            if ref != pid and ref not in merged_ids:
                violations.append(f"{pid}: orphan ref '{ref}'")

    # Check skeleton pages
    for skel in skeletons:
        if not isinstance(skel, dict):
            continue
        page = skel.get("page", skel) if "page" in skel else skel
        if not isinstance(page, dict):
            continue
        pid = page.get("id", "?")
        for ref in _extract_ref_ids(page.get("references", [])):
            if ref != pid and ref not in merged_ids:
                violations.append(f"{pid}: orphan ref '{ref}'")

    valid = len(violations) == 0
    return {
        "gate_result": {"valid": valid, "violations": violations},
    }
