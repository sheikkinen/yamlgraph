"""Deterministic reducer for the FR-892 corpus census demo."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

ERROR_STRINGS = ("Error:", "No results")
MODEL = "claude-haiku-4-5"
PROMPT_VERSION = "judge_item.v1"
SYNTHESIS_MODEL = "claude-haiku-4-5"
SYNTHESIS_PROMPT_VERSION = "synthesize_brief.v1"

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class LedgerRow(BaseModel):
    """One fail-closed census ledger row."""

    item_ref: str = Field(min_length=1)
    judgement: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    evidence_span: str
    model: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    abstained: bool
    abstain_reason: str
    disagreement: bool

    @field_validator("*", mode="before")
    @classmethod
    def _strip_required_strings(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def _validate_abstention_cells(self) -> LedgerRow:
        if self.abstained:
            if self.evidence_span:
                raise ValueError("evidence_span must be empty when abstained")
            if not self.abstain_reason:
                raise ValueError("abstain_reason is required when abstained")
        else:
            if not self.evidence_span:
                raise ValueError("evidence_span is required unless abstained")
            if self.abstain_reason:
                raise ValueError("abstain_reason must be empty when not abstained")
        return self


def _rows_by_index(items: list[str], findings: list[dict[str, Any]]) -> list[LedgerRow]:
    rows: list[LedgerRow] = []
    seen: set[int] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("finding must be a dict")
        if "_error" in finding:
            raise ValueError(f"finding contains map error: {finding['_error']}")

        index = finding.get("source_index")
        if index is None:
            index = finding.get("_map_index")
        if not isinstance(index, int):
            raise ValueError("finding missing source_index")
        if index < 0 or index >= len(items):
            raise ValueError(f"finding index out of range: {index}")
        if index in seen:
            raise ValueError(f"duplicate finding for item index {index}")
        seen.add(index)

        judgement = str(finding.get("judgement", "")).strip()
        if any(marker in judgement for marker in ERROR_STRINGS):
            raise ValueError("judgement is an error string")

        try:
            row = LedgerRow(
                item_ref=items[index],
                judgement=judgement,
                confidence=finding.get("confidence"),
                evidence_span=str(finding.get("evidence_span", "")).strip(),
                model=MODEL,
                prompt_version=PROMPT_VERSION,
                abstained=bool(finding.get("abstained")),
                abstain_reason=str(finding.get("abstain_reason", "")).strip(),
                disagreement=False,
            )
        except ValidationError as exc:
            raise ValueError(
                f"invalid ledger row for item {items[index]}: {exc}"
            ) from exc
        rows.append(row)

    missing = sorted(set(range(len(items))) - seen)
    if missing:
        raise ValueError(f"missing findings for item indexes: {missing}")
    return sorted(rows, key=lambda row: row.item_ref)


def _cell(value: Any) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()


def _write_artifacts(rows: list[LedgerRow], output_path: str) -> dict[str, Any]:
    markdown_path = Path(output_path)
    if not markdown_path.suffix:
        markdown_path = markdown_path.with_suffix(".md")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = markdown_path.with_suffix(".jsonl")

    header = (
        "| item_ref | judgement | confidence | evidence_span | model | "
        "prompt_version | abstained | abstain_reason | disagreement |"
    )
    lines = [
        "# Corpus Census Ledger",
        "",
        header,
        "|---|---|---:|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(row.item_ref),
                    _cell(row.judgement),
                    f"{row.confidence:.3f}",
                    _cell(row.evidence_span),
                    _cell(row.model),
                    _cell(row.prompt_version),
                    str(row.abstained).lower(),
                    _cell(row.abstain_reason),
                    str(row.disagreement).lower(),
                )
            )
            + " |"
        )
    markdown_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.model_dump(), sort_keys=True) + "\n")

    return {
        "markdown_path": str(markdown_path),
        "jsonl_path": str(jsonl_path),
        "rows": len(rows),
    }


def reduce_ledger(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Validate findings and write markdown plus JSONL ledger artifacts."""
    effective_state = state if isinstance(state, dict) else kwargs
    items = effective_state.get("items")
    findings = effective_state.get("findings")
    output_path = effective_state.get("output_path")
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("output_path must be a non-empty string")

    rows = _rows_by_index([str(item) for item in items], findings)
    return {"ledger": _write_artifacts(rows, output_path)}


def _require_non_empty_string(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required variable: {key}")
    return value.strip()


def _load_jsonl_rows(jsonl_path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(jsonl_path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if not isinstance(row, dict):
                raise ValueError(f"ledger row {line_number} must be a JSON object")
            rows.append(row)
    return rows


def prepare_brief_input(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Load the reduced ledger and prepare bounded synthesis input."""
    from examples.demos.corpus_census.adapters import census_brief

    effective_state = state if isinstance(state, dict) else kwargs
    _require_non_empty_string(effective_state, "brief_path")
    _require_non_empty_string(effective_state, "brief_rubric")

    ledger = effective_state.get("ledger")
    if not isinstance(ledger, dict):
        raise ValueError("ledger must be a dict")
    jsonl_path = _require_non_empty_string(ledger, "jsonl_path")
    rows = _load_jsonl_rows(jsonl_path)
    return {"brief_input": census_brief.build_synthesis_input(rows)}


def render_brief(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Render a citation-checked human brief from structured claims."""
    from examples.demos.corpus_census.adapters import census_brief

    effective_state = state if isinstance(state, dict) else kwargs
    brief_path = _require_non_empty_string(effective_state, "brief_path")
    brief_input = effective_state.get("brief_input")
    if not isinstance(brief_input, list):
        raise ValueError("brief_input must be a list")

    claims_output = effective_state.get("claims")
    if not isinstance(claims_output, dict):
        raise ValueError("claims must be a dict")
    claims = claims_output.get("claims")
    if not isinstance(claims, list):
        raise ValueError("claims.claims must be a list")

    ledger = effective_state.get("ledger")
    if not isinstance(ledger, dict):
        raise ValueError("ledger must be a dict")
    source_jsonl_path = _require_non_empty_string(ledger, "jsonl_path")

    result = census_brief.emit_brief(
        claims,
        brief_input,
        brief_path,
        run_meta={
            "model": SYNTHESIS_MODEL,
            "prompt_version": SYNTHESIS_PROMPT_VERSION,
            "rows": len(brief_input),
            "source_jsonl_path": source_jsonl_path,
        },
    )
    return {"brief": result}
