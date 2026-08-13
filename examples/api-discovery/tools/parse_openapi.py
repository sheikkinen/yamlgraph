"""parse_openapi — OpenAPI/Swagger spec parser for API discovery (FR-783).

Deterministic parsing, no LLM. tool_call-compatible kwargs callable.

Contract: ``parse_openapi(spec_json: str | dict) -> dict``
  Returns ``{"endpoints": [...], "info": {"title": ..., "version": ...}}``.
  Raises ``ValueError`` for invalid JSON, non-object specs, and
  missing/invalid ``paths`` key.
"""

from __future__ import annotations

import json


def parse_openapi(spec_json: str | dict) -> dict:
    """Parse an OpenAPI/Swagger JSON spec into an endpoint inventory."""
    if isinstance(spec_json, str):
        try:
            spec = json.loads(spec_json)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"invalid JSON: {e}") from e
    else:
        spec = spec_json

    if not isinstance(spec, dict):
        raise ValueError(f"spec must be a JSON object, got {type(spec).__name__}")

    paths = spec.get("paths")
    if paths is None:
        raise ValueError("spec missing required 'paths' key")
    if not isinstance(paths, dict):
        raise ValueError(f"'paths' must be a JSON object, got {type(paths).__name__}")

    endpoints = []
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.startswith("x-") or method == "parameters":
                continue
            if not isinstance(operation, dict):
                continue
            endpoints.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "description": operation.get(
                        "description", operation.get("summary", "")
                    ),
                    "parameters": [
                        p.get("name", "")
                        for p in operation.get("parameters", [])
                        if isinstance(p, dict)
                    ],
                }
            )

    info = spec.get("info", {})
    return {
        "endpoints": endpoints,
        "info": {
            "title": info.get("title") if isinstance(info, dict) else None,
            "version": info.get("version") if isinstance(info, dict) else None,
        },
    }
