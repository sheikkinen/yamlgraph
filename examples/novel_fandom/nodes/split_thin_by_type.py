"""Split thin entities by type for routing (FR-657).

Partitions state.thin_entities into state.thin_events and
state.thin_other so the graph can route events to the agent node
and other types to the existing LLM map node.
"""

from __future__ import annotations

from typing import Any


def split_thin_by_type(state: dict[str, Any]) -> dict[str, Any]:
    """Partition thin_entities into thin_events and thin_other."""
    thin = state.get("thin_entities", [])
    thin_events = [e for e in thin if e.get("entity_type") == "event"]
    thin_other = [e for e in thin if e.get("entity_type") != "event"]
    return {"thin_events": thin_events, "thin_other": thin_other}
