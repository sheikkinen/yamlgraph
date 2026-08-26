"""Deterministic reducer for the FR-892 corpus census demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

ERROR_STRINGS = ("Error:", "No results")
MODEL = "claude-haiku-4-5"
PROMPT_VERSION = "judge_item.v1"


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
