"""Constrainability of prompt output schemas (FR-1123, FR-1125).

Anthropic constrained decoding (``output_config.format``, the method FR-998
forces for Anthropic models) cannot express two shapes a prompt schema can
declare:

- **untyped** — a subschema with none of ``type``/``anyOf``/``oneOf``/``allOf``/
  ``$ref`` (what ``Any`` and ``list[Any]`` produce). The SDK transform raises
  before any request, naming neither prompt nor field (FR-1123).
- **open_object** — ``type: object`` with no declared ``properties`` (what
  ``dict``, ``dict[str, Any]`` and ``list[dict]`` produce). The API rejects
  ``additionalProperties: true``, so the SDK transform rewrites the object to
  ``{"type": "object", "properties": {}, "additionalProperties": false}``:
  a grammar whose only instance is ``{}``. The call succeeds and the model
  answers empty (FR-1125; spike ``docs/spikes/constrained-object-2026-09-27``).

This module states both rules once, traversing exactly as the SDK transform
does, plus the one static provider resolution used by ``create_llm``, compile
and lint so all three agree on whether a node is Anthropic-bound.

Pure: no LLM, provider or executor imports (the linter imports this module).
"""

from __future__ import annotations

import os
import re
from typing import Any, Literal, NamedTuple

DEFAULT_PROVIDER = "anthropic"
ROOT_PATH = "(root)"
_STATE_REF = re.compile(r"\{state\.[^}]+\}")
_COMPOSITIONS = ("anyOf", "oneOf", "allOf")

Kind = Literal["untyped", "open_object"]


class SchemaFinding(NamedTuple):
    """One subschema constrained decoding cannot express: its path and why."""

    path: str
    kind: Kind


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


def find_unconstrainable(schema: dict) -> list[SchemaFinding]:
    """Every untyped or open-object subschema, in walk order, each path once."""
    found: list[SchemaFinding] = []
    _walk(schema, [], found)
    return found


def find_untyped_subschemas(schema: dict) -> list[str]:
    """JSON paths of subschemas lacking type/anyOf/oneOf/allOf/$ref (FR-1123)."""
    return [f.path for f in find_unconstrainable(schema) if f.kind == "untyped"]


def find_open_objects(schema: dict) -> list[str]:
    """JSON paths of ``type: object`` subschemas with no declared properties (FR-1125)."""
    return [f.path for f in find_unconstrainable(schema) if f.kind == "open_object"]


def _walk(schema: dict, path: list[str], found: list[SchemaFinding]) -> None:
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
            found.append(SchemaFinding(".".join(path) or ROOT_PATH, "untyped"))
            return
    kind = schema.get("type")
    if kind == "object":
        properties = schema.get("properties") or {}
        if not properties:
            found.append(SchemaFinding(".".join(path) or ROOT_PATH, "open_object"))
            return
        for key, sub in properties.items():
            _walk(sub, [*path, key], found)
    elif kind == "array" and isinstance(schema.get("items"), dict):
        _walk(schema["items"], [*path, "items"], found)


_FIX: dict[Kind, str] = {
    "untyped": (
        "has no type; Anthropic constrained decoding rejects untyped subschemas. "
        "Declare a concrete type (e.g. list[str]) or a nested schema with "
        "declared properties."
    ),
    "open_object": (
        "is an object with no declared properties; Anthropic constrained "
        "decoding reduces it to {} and the model can only answer empty. Declare "
        "its properties with the output_schema form "
        "(items: {type: object, properties: {...}}) or use a provider that "
        "accepts open objects."
    ),
}


def _coerce(findings: list[SchemaFinding] | list[str]) -> list[SchemaFinding]:
    return [
        f if isinstance(f, SchemaFinding) else SchemaFinding(f, "untyped")
        for f in findings
    ]


def refusal_message(subject: str, findings: list[SchemaFinding] | list[str]) -> str:
    """The one wording used by compile, bind and lint; one clause per finding.

    Plain strings are FR-1123 callers naming untyped paths.
    """
    clauses = [f"field '{f.path}' {_FIX[f.kind]}" for f in _coerce(findings)]
    return f"{subject}: " + " ".join(clauses)


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
    findings = find_unconstrainable(output_model.model_json_schema())
    if findings:
        subject = node_subject(node, cfg.prompt_name, cfg.model)
        raise UnconstrainableSchemaError(refusal_message(subject, findings))
