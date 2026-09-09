"""FR-1034: effective provider/model for the census synthesis call.

A census has two LLM stages with opposite shapes — many tiny per-item
classifications and one long structured synthesis — so a model that suits one
often cannot serve the other. This resolver lets the synthesis call be selected
independently while leaving the per-item call alone.

Its own module rather than ``tools.py`` because that file is already exactly
450 lines, the repository's hard module maximum.
"""

from __future__ import annotations

from typing import Any


def _required(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"resolve_brief_llm: {key} is required and must be non-empty"
        )
    return value.strip()


def _override(state: dict[str, Any], key: str) -> str | None:
    """A blank override is absent, not a value named empty."""
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def resolve_brief_llm(state: dict[str, Any]) -> dict[str, str]:
    """Return the provider/model the synthesis call should use.

    ``brief_provider`` and ``brief_model`` fall back **independently** to the
    base pair, so overriding only the model keeps the base provider.
    """
    provider = _required(state, "provider")
    model = _required(state, "model")
    return {
        "provider": _override(state, "brief_provider") or provider,
        "model": _override(state, "brief_model") or model,
    }


def resolved_brief_model(state: dict[str, Any]) -> str:
    """The model that actually produced the brief (REQ-YG-675).

    Never falls back to ``state["model"]``: that is the per-item map model, and
    stamping it would label a brief with a model that did not write it.
    """
    brief_llm = state.get("brief_llm")
    if not isinstance(brief_llm, dict):
        raise ValueError(
            "render_brief: brief_llm must be a mapping resolved by "
            "resolve_brief_llm before synthesis"
        )
    model = brief_llm.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("render_brief: brief_llm.model is missing or blank")
    return model.strip()
