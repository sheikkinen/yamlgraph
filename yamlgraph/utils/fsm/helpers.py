"""Helper functions for FSM bridge actions."""

from __future__ import annotations

from typing import Any


def extract_event(raw: Any, event_map: dict[str, str]) -> str | None:
    """Extract an FSM event from raw graph output using *event_map*."""
    if isinstance(raw, str):
        candidate = raw.strip().lower()
        return event_map.get(candidate)

    if hasattr(raw, "model_dump"):
        for field_value in raw.model_dump().values():
            if isinstance(field_value, str):
                candidate = field_value.strip().lower()
                mapped = event_map.get(candidate)
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
