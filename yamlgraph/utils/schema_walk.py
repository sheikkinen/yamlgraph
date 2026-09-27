"""Constrainability of prompt output schemas (FR-1123).

Anthropic's strict schema transform refuses a subschema that carries none of
``type``/``anyOf``/``oneOf``/``allOf``/``$ref`` — what ``Any`` and
``list[Any]`` produce — before any request, naming neither prompt nor field.
This module states that rule once, traversing exactly as the SDK transform
does, and the one static provider resolution used by ``create_llm``, compile
and lint so all three agree on whether a node is Anthropic-bound.

Pure: no LLM, provider or executor imports (the linter imports this module).
"""

from __future__ import annotations

import os
import re
from typing import Any

DEFAULT_PROVIDER = "anthropic"
ROOT_PATH = "(root)"
_STATE_REF = re.compile(r"\{state\.[^}]+\}")
_COMPOSITIONS = ("anyOf", "oneOf", "allOf")


class UnconstrainableSchemaError(ValueError):
    """A prompt schema carries a subschema constrained decoding cannot express."""


def resolve_static_provider(
    node_provider: str | None, default_provider: str | None = None
) -> str | None:
    """Provider knowable before execution: node, defaults, ``PROVIDER``, built-in.

    A ``{state.x}`` reference is decided at run time, so it resolves to ``None``.
    """
    for candidate in (node_provider, default_provider):
        if candidate:
            return None if _STATE_REF.search(candidate) else candidate
    return os.getenv("PROVIDER") or DEFAULT_PROVIDER


def find_untyped_subschemas(schema: dict) -> list[str]:
    """JSON paths of subschemas lacking type/anyOf/oneOf/allOf/$ref, in walk order."""
    found: list[str] = []
    _walk(schema, [], found)
    return found


def _walk(schema: dict, path: list[str], found: list[str]) -> None:
    for name, sub in (schema.get("$defs") or {}).items():
        _walk(sub, [*path, "$defs", name], found)
    if "$ref" in schema:
        return
    for keyword in _COMPOSITIONS:
        variants = schema.get(keyword)
        if isinstance(variants, list):
            for i, variant in enumerate(variants):
                _walk(variant, [*path, f"{keyword}[{i}]"], found)
            break
    else:
        if schema.get("type") is None:
            found.append(".".join(path) or ROOT_PATH)
            return
    kind = schema.get("type")
    if kind == "object":
        for key, sub in (schema.get("properties") or {}).items():
            _walk(sub, [*path, key], found)
    elif kind == "array" and isinstance(schema.get("items"), dict):
        _walk(schema["items"], [*path, "items"], found)


def refusal_message(subject: str, paths: list[str]) -> str:
    """The one wording used by compile, bind and lint."""
    where = ", ".join(f"'{p}'" for p in paths)
    return (
        f"{subject}: field {where} has no type; "
        "Anthropic constrained decoding rejects untyped subschemas. "
        "Declare a concrete type (e.g. list[dict], list[str]) or a nested schema."
    )


def node_subject(node: str, prompt: str | None, model: str | None) -> str:
    return f"Prompt '{prompt}' (node '{node}', model '{model or 'provider default'}')"


def refuse_static_anthropic_node(node: str, cfg: Any) -> None:
    """Compile-time refusal for a node statically bound to Anthropic.

    *cfg* is an ``LLMNodeConfig`` (duck-typed: this module imports no factory).
    """
    output_model = cfg.output_model
    provider = resolve_static_provider(cfg.provider, cfg.default_provider)
    if output_model is None or provider != "anthropic":
        return
    paths = find_untyped_subschemas(output_model.model_json_schema())
    if paths:
        subject = node_subject(node, cfg.prompt_name, cfg.model)
        raise UnconstrainableSchemaError(refusal_message(subject, paths))
