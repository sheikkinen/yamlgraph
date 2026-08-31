"""FR-943 failure taxonomy helpers for the corpus census reducer.

Demo-scoped (no shared framework API): closed classification of
Pydantic validation errors into model-owned vs structural, frozen
reason formatting/truncation, and deterministic raw-finding
serialization for the contained-row evidence contract.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

MAX_FAILURE_REASON_CHARS = 240
_REASON_PREFIX = "row failed: "
# loc == () is the model-level abstention validator — model-owned.
MODEL_OWNED_FIELDS = frozenset(
    {"judgement", "confidence", "evidence_span", "abstained", "abstain_reason"}
)


def is_model_owned(exc: ValidationError) -> bool:
    """True iff every error location is () or rooted in a model-owned field."""
    entries = exc.errors()
    if not entries:
        return False
    for entry in entries:
        loc = entry.get("loc", ())
        if loc == ():
            continue
        if not loc or loc[0] not in MODEL_OWNED_FIELDS:
            return False
    return True


def first_error_reason(exc: ValidationError) -> str:
    """Frozen format for the first emitted error: <location>: <msg> [<type>]."""
    entry = exc.errors()[0]
    location = ".".join(str(part) for part in entry.get("loc", ())) or "<model>"
    return f"{location}: {entry.get('msg', '')} [{entry.get('type', '')}]"


def failure_reason(reason: str) -> str:
    """Prefix and bound the human-facing reason; evidence is never truncated."""
    full = _REASON_PREFIX + reason
    if len(full) <= MAX_FAILURE_REASON_CHARS:
        return full
    return full[: MAX_FAILURE_REASON_CHARS - 3] + "..."


def serialize_finding(finding: dict[str, Any]) -> str:
    """Deterministic JSON of the complete finding; raises TypeError if not serializable."""
    return json.dumps(
        finding, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def failed_row_values(reason: str, raw_judgement: str) -> dict[str, Any]:
    """Frozen contained-row cells (item_ref/model/prompt_version added by caller)."""
    return {
        "judgement": "abstain",
        "confidence": 0.0,
        "evidence_span": "",
        "abstained": True,
        "abstain_reason": failure_reason(reason),
        "disagreement": False,
        "raw_judgement": raw_judgement,
        "repaired": False,
    }
