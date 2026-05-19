"""Helper functions for FSM bridge actions."""

from __future__ import annotations

from typing import Any


def extract_event(raw: Any, event_map: dict[str, str]) -> str | None:
    """Extract an FSM event from raw graph output using *event_map*.

    Matching order (first hit wins):
    1. Exact stripped/lowercased match of the whole value.
    2. Each line scanned in order — first exact line match wins.

    For ``str`` input, lines are scanned directly.
    For ``dict`` / Pydantic model inputs, each string field value is scanned
    line-by-line.  This handles ``CopilotResult.output`` where the verdict
    keyword appears on its own line but is preceded by preamble text.

    Accepted input types:
    - ``str`` — scanned directly.
    - ``dict`` — string field values scanned in insertion order.
    - Pydantic model — converted via ``model_dump()`` then treated as dict.
    """
    if isinstance(raw, str):
        candidate = raw.strip().lower()
        mapped = event_map.get(candidate)
        if mapped:
            return mapped
        for line in candidate.splitlines():
            mapped = event_map.get(line.strip())
            if mapped:
                return mapped
        return None

    # Handles plain dict (LangGraph serialized state) and Pydantic models uniformly.
    d: dict | None = (
        raw
        if isinstance(raw, dict)
        else (raw.model_dump() if hasattr(raw, "model_dump") else None)
    )
    if d is not None:
        for field_value in d.values():
            if isinstance(field_value, str):
                candidate = field_value.strip().lower()
                mapped = event_map.get(candidate)
                if mapped:
                    return mapped
                for line in candidate.splitlines():
                    mapped = event_map.get(line.strip())
                    if mapped:
                        return mapped

    return None


def json_safe(value: Any) -> Any:
    """Convert values into JSON-serializable primitives."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [json_safe(item) for item in value]
    if hasattr(value, "model_dump"):
        return json_safe(value.model_dump())
    return str(value)


def resolve_context_ref(
    value: Any,
    context: dict[str, Any],
    *,
    missing: Any | None = None,
) -> Any:
    """Resolve ``{key}`` references against FSM context."""
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        key = value[1:-1]
        return context.get(key, missing if missing is not None else value)
    return value


def has_pending_next(state: Any) -> bool:
    """Return True if a checkpointed graph has pending interrupt targets."""
    next_nodes = getattr(state, "next", None)
    return bool(next_nodes)
