"""FR-1028: root-graph ``defaults`` override applied at the load boundary.

Only ``provider`` and ``model`` are reachable; explicit node pins keep
precedence downstream because they are resolved before ``defaults``.
"""

from __future__ import annotations


def apply_default_overrides(
    config: dict, provider_override: str | None, model_override: str | None
) -> dict:
    """Return a copy of ``config`` with the named defaults replaced; never mutates."""
    if provider_override is None and model_override is None:
        return config
    config = dict(config)
    defaults = dict(config.get("defaults") or {})
    if provider_override is not None:
        defaults["provider"] = provider_override
    if model_override is not None:
        defaults["model"] = model_override
    config["defaults"] = defaults
    return config
