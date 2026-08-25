"""Deterministic tools for the FR-884 session-shapes demo."""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

SHAPES = (
    "plan-fr",
    "judge-fr",
    "enforce-fr",
    "review-pr",
    "deploy-watch",
    "test-orchestration",
    "incident-forensics",
    "docs-drafting",
    "repo-ops",
    "backlog-ops",
    "research",
    "introspection",
)
OUTPUT_PATH = Path("tmp/fr884-classified.json")


class SessionRow(BaseModel):
    session_id: str = Field(min_length=1)
    workspace: str
    requests: int = Field(ge=0)
    prompt_tokens: int = Field(ge=0)
    fork_prefix_dropped: int = Field(ge=0)
    skeleton: str = Field(min_length=1)


class ShapeFraction(BaseModel):
    shape: str
    fraction: float = Field(ge=0.0, le=1.0)

    @field_validator("shape")
    @classmethod
    def shape_is_known(cls, value: str) -> str:
        if value not in SHAPES:
            raise ValueError(f"unknown shape: {value}")
        return value


class ShapeClassification(BaseModel):
    primary_shape: str
    shape_mix: list[ShapeFraction] = Field(min_length=1)

    @field_validator("primary_shape")
    @classmethod
    def primary_shape_is_known(cls, value: str) -> str:
        if value not in SHAPES:
            raise ValueError(f"unknown primary_shape: {value}")
        return value

    @field_validator("shape_mix")
    @classmethod
    def fractions_sum_to_one(cls, value: list[ShapeFraction]) -> list[ShapeFraction]:
        total = sum(item.fraction for item in value)
        if not 0.95 <= total <= 1.05:
            raise ValueError(f"shape_mix fractions must sum near 1.0, got {total:.3f}")
        return value


def load_sessions(state: dict[str, Any]) -> dict[str, Any]:
    """Read JSONL session skeletons and return map-ready session rows."""
    input_file = state.get("input_file")
    if not isinstance(input_file, str) or not input_file.strip():
        raise ValueError("input_file is required")

    path = Path(input_file)
    if not path.is_file():
        raise FileNotFoundError(f"input_file does not exist: {path}")

    sessions: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row") from exc
            try:
                row = SessionRow.model_validate(raw)
            except ValidationError as exc:
                raise ValueError(
                    f"{path}:{line_number}: invalid session row: {exc}"
                ) from exc
            sessions.append(row.model_dump())

    if not sessions:
        raise ValueError(f"input_file contains no session rows: {path}")

    return {"sessions": sessions, "session_count": len(sessions)}


def aggregate_classifications(state: dict[str, Any]) -> dict[str, Any]:
    """Aggregate map classifications and write the privacy-preserving JSON report."""
    sessions = _session_rows_by_id(state.get("sessions"))
    classifications = _normalized_classifications(
        state.get("classifications"), sessions
    )

    primary_counts: Counter[str] = Counter()
    token_weighted: defaultdict[str, float] = defaultdict(float)
    session_shapes: list[dict[str, str]] = []
    total_tokens = sum(row.prompt_tokens for row in sessions.values())

    for item in classifications:
        session = sessions[item["session_id"]]
        classification = item["classification"]
        primary_counts[classification.primary_shape] += 1
        session_shapes.append(
            {
                "session_id": item["session_id"],
                "primary_shape": classification.primary_shape,
            }
        )
        for mix in classification.shape_mix:
            token_weighted[mix.shape] += session.prompt_tokens * mix.fraction

    result = {
        "session_count": len(sessions),
        "classified_count": len(classifications),
        "primary_counts": [
            {"shape": shape, "count": primary_counts[shape]}
            for shape in SHAPES
            if primary_counts[shape]
        ],
        "token_weighted_share": [
            {
                "shape": shape,
                "share": round(token_weighted[shape] / total_tokens, 6)
                if total_tokens
                else 0.0,
            }
            for shape in SHAPES
            if token_weighted[shape]
        ],
        "sessions": sorted(session_shapes, key=lambda item: item["session_id"]),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return {"result": result, "sessions": []}


def _session_rows_by_id(raw_sessions: Any) -> dict[str, SessionRow]:
    if not isinstance(raw_sessions, list):
        raise ValueError("sessions must be a list")

    sessions: dict[str, SessionRow] = {}
    for raw in raw_sessions:
        row = SessionRow.model_validate(raw)
        if row.session_id in sessions:
            raise ValueError(f"duplicate session_id: {row.session_id}")
        sessions[row.session_id] = row
    return sessions


def _normalized_classifications(
    raw_items: Any, sessions: dict[str, SessionRow]
) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        raise ValueError("classifications must be a list")
    if len(raw_items) != len(sessions):
        raise ValueError(
            f"classification count mismatch: {len(raw_items)} classifications for "
            f"{len(sessions)} sessions"
        )

    ordered_session_ids = list(sessions)
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in sorted(raw_items, key=lambda item: item.get("_map_index", 0)):
        if not isinstance(raw, dict):
            raise ValueError(f"classification item must be a dict, got {type(raw)}")
        if "_error" in raw:
            raise ValueError(f"map classification failed: {raw['_error']}")

        index = raw.get("_map_index")
        if not isinstance(index, int) or not 0 <= index < len(ordered_session_ids):
            raise ValueError(f"classification has invalid _map_index: {index}")
        session_id = ordered_session_ids[index]
        if session_id in seen:
            raise ValueError(f"duplicate classification for session_id: {session_id}")

        payload = raw.get("classification") or raw
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        classification = ShapeClassification.model_validate(_normalize_payload(payload))
        seen.add(session_id)
        normalized.append({"session_id": session_id, "classification": classification})

    missing = sorted(set(sessions) - seen)
    if missing:
        raise ValueError(
            "missing classifications for session_id: " + ", ".join(missing)
        )
    return normalized


def _normalize_payload(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)
    raw_mix = normalized.get("shape_mix")
    if isinstance(raw_mix, list):
        mix: list[Any] = []
        for raw_item in raw_mix:
            if (
                isinstance(raw_item, dict)
                and "shape" not in raw_item
                and "shape_id" in raw_item
            ):
                item = dict(raw_item)
                item["shape"] = item.pop("shape_id")
                mix.append(item)
            else:
                mix.append(raw_item)
        normalized["shape_mix"] = mix
    return normalized
