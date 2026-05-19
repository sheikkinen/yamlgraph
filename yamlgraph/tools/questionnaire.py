"""Built-in questionnaire utilities for schema-driven probing loops."""

from __future__ import annotations

from typing import Any

__all__ = ["detect_gaps", "normalize_extracted"]


def detect_gaps(state: dict[str, Any]) -> dict[str, Any]:
    """Detect required schema fields missing from extracted values.

    Required field values are considered missing when value is ``None`` or ``""``.
    """
    schema = state.get("schema")
    fields = schema.get("fields", []) if isinstance(schema, dict) else []

    extracted_value = state.get("extracted")
    extracted = extracted_value if isinstance(extracted_value, dict) else {}

    gaps: list[str] = []
    for field in fields:
        if not field.get("required"):
            continue
        field_id = field["id"]
        value = extracted.get(field_id)
        if value is None or value == "":
            gaps.append(field_id)

    gaps.sort()
    # Intentionally excludes probe_count; probing cadence belongs in graph state.
    return {"gaps": gaps, "has_gaps": bool(gaps)}


def normalize_extracted(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Normalize extracted state to a dict when upstream output is malformed."""
    extracted = state.get("extracted")
    if isinstance(extracted, dict):
        return {}
    return {"extracted": {}}
