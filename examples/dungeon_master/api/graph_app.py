"""Compiled-graph cache + result-normalization helpers for DM v2.

Shared by the stage adapter (``session``) and the play loop (``turn_ops``) so
both run stage graphs through one cache and normalize model output the same way.
Kept dependency-free (no session/turn imports) to avoid an import cycle.
"""

from __future__ import annotations

_app_cache: dict[str, object] = {}


def reset_caches() -> None:
    """Reset the compiled-graph cache (for testing)."""
    _app_cache.clear()


def get_app(graph: str):
    """Compile + cache a stage graph (no checkpointer)."""
    if graph not in _app_cache:
        from yamlgraph.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(graph)
        _app_cache[graph] = compile_graph(config).compile()
    return _app_cache[graph]


def clean_text(value: object) -> str:
    """Normalize a raw model result to plain string, stripping a stray fence."""
    text = str(value or "").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def field(obj: object, key: str) -> str:
    """Read a field from a map-result item (a dict or a pydantic-ish object)."""
    if isinstance(obj, dict):
        return str(obj.get(key, "") or "")
    return str(getattr(obj, key, "") or "")
