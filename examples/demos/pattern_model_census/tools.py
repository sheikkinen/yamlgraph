"""Deterministic reducer for the FR-896 pattern/model census demo."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

MODEL = "mercury-2"
PATTERN_PROMPT_VERSION = "judge_pattern.v1"
MODEL_PROMPT_VERSION = "judge_model.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]


class CommitMetadata(BaseModel):
    """Commit metadata allowed into the private working ledger."""

    model_config = ConfigDict(extra="forbid")

    repo: str = Field(min_length=1)
    sha: str = Field(min_length=1)
    date: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    shortstat: str = ""


class LedgerRow(BaseModel):
    """One private working-ledger row for one commit/lens judgement."""

    model_config = ConfigDict(extra="forbid")

    repo_alias: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    sha: str = Field(min_length=1)
    quarter: str = Field(min_length=1)
    lens: str = Field(pattern="^(pattern|model)$")
    label: str | None = None
    subject: str = Field(min_length=1)
    shortstat: str = ""
    model: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)


def _require_list(state: dict[str, Any], key: str) -> list[Any]:
    value = state.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_non_empty_string(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _quarter(date_text: str) -> str:
    parsed = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    quarter = ((parsed.month - 1) // 3) + 1
    return f"{parsed.year}-Q{quarter}"


def _inside_yamlgraph_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return False
    return True


def _assert_allowed_output_path(output_path: str) -> Path:
    markdown_path = Path(output_path)
    if not markdown_path.suffix:
        markdown_path = markdown_path.with_suffix(".md")
    resolved = markdown_path.resolve()
    if _inside_yamlgraph_repo(resolved):
        tmp_root = (REPO_ROOT / "tmp").resolve()
        try:
            resolved.relative_to(tmp_root)
        except ValueError:
            raise ValueError(
                "output_path inside yamlgraph must be under tmp/ for this demo"
            ) from None
    return markdown_path


def _metadata_by_index(contents: list[Any]) -> list[CommitMetadata]:
    rows: list[CommitMetadata] = []
    for index, content in enumerate(contents):
        if not isinstance(content, dict):
            raise ValueError(f"content {index} must be a dict")
        if "_error" in content:
            raise ValueError(f"content {index} contains map error: {content['_error']}")
        data = {key: value for key, value in content.items() if key != "_map_index"}
        try:
            rows.append(CommitMetadata.model_validate(data))
        except ValidationError as exc:
            raise ValueError(
                f"invalid commit metadata at index {index}: {exc}"
            ) from exc
    return rows


def _labels_by_index(
    findings: list[Any], *, key: str, expected_count: int
) -> dict[int, str | None]:
    labels: dict[int, str | None] = {}
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError(f"{key} finding must be a dict")
        if "_error" in finding:
            raise ValueError(f"{key} finding contains map error: {finding['_error']}")
        index = finding.get("_map_index")
        if not isinstance(index, int):
            raise ValueError(f"{key} finding missing _map_index")
        if index < 0 or index >= expected_count:
            raise ValueError(f"{key} finding index out of range: {index}")
        if index in labels:
            raise ValueError(f"duplicate {key} finding for item index {index}")
        label = finding.get(key)
        if label is not None and not isinstance(label, str):
            raise ValueError(f"{key} finding label must be a string or null")
        labels[index] = (
            label.strip() if isinstance(label, str) and label.strip() else None
        )
    missing = sorted(set(range(expected_count)) - set(labels))
    if missing:
        raise ValueError(f"missing {key} findings for item indexes: {missing}")
    return labels


def _ledger_rows(
    *,
    repo_alias: str,
    contents: list[CommitMetadata],
    pattern_labels: dict[int, str | None],
    model_labels: dict[int, str | None],
) -> list[LedgerRow]:
    rows: list[LedgerRow] = []
    for index, content in enumerate(contents):
        rows.append(
            LedgerRow(
                repo_alias=repo_alias,
                repo=content.repo,
                sha=content.sha,
                quarter=_quarter(content.date),
                lens="pattern",
                label=pattern_labels[index],
                subject=content.subject,
                shortstat=content.shortstat,
                model=MODEL,
                prompt_version=PATTERN_PROMPT_VERSION,
            )
        )
        rows.append(
            LedgerRow(
                repo_alias=repo_alias,
                repo=content.repo,
                sha=content.sha,
                quarter=_quarter(content.date),
                lens="model",
                label=model_labels[index],
                subject=content.subject,
                shortstat=content.shortstat,
                model=MODEL,
                prompt_version=MODEL_PROMPT_VERSION,
            )
        )
    return rows


def _cell(value: Any) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()


def _write_artifacts(rows: list[LedgerRow], output_path: str) -> dict[str, Any]:
    markdown_path = _assert_allowed_output_path(output_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = markdown_path.with_suffix(".jsonl")

    counts = Counter(
        (
            row.repo_alias,
            row.quarter,
            row.lens,
            row.label if row.label is not None else "unlabeled",
        )
        for row in rows
    )
    lines = [
        "# Pattern/Model Census Summary",
        "",
        "| repo_alias | quarter | lens | label | count |",
        "|---|---|---|---|---:|",
    ]
    for (repo_alias, quarter, lens, label), count in sorted(counts.items()):
        lines.append(
            f"| {_cell(repo_alias)} | {_cell(quarter)} | {_cell(lens)} | "
            f"{_cell(label)} | {count} |"
        )
    markdown_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.model_dump(), sort_keys=True) + "\n")

    return {
        "markdown_path": str(markdown_path),
        "jsonl_path": str(jsonl_path),
        "rows": len(rows),
        "summary_rows": len(counts),
    }


def reduce_ledger(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Join map findings by index and write private JSONL plus public-safe summary."""
    effective_state = state if isinstance(state, dict) else kwargs
    repo_alias = _require_non_empty_string(effective_state, "repo_alias")
    output_path = _require_non_empty_string(effective_state, "output_path")
    contents = _metadata_by_index(_require_list(effective_state, "contents"))
    pattern_labels = _labels_by_index(
        _require_list(effective_state, "pattern_findings"),
        key="pattern",
        expected_count=len(contents),
    )
    model_labels = _labels_by_index(
        _require_list(effective_state, "model_findings"),
        key="model_mentioned",
        expected_count=len(contents),
    )
    rows = _ledger_rows(
        repo_alias=repo_alias,
        contents=contents,
        pattern_labels=pattern_labels,
        model_labels=model_labels,
    )
    return {"ledger": _write_artifacts(rows, output_path)}


def mark_patterns_complete(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, bool]:
    """Barrier node: fail unless one pattern finding exists for each content item."""
    effective_state = state if isinstance(state, dict) else kwargs
    contents = _require_list(effective_state, "contents")
    _labels_by_index(
        _require_list(effective_state, "pattern_findings"),
        key="pattern",
        expected_count=len(contents),
    )
    return {"pattern_pass_complete": True}


def mark_extraction_complete(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, bool]:
    """Barrier node: fail unless each discovered item has commit metadata."""
    effective_state = state if isinstance(state, dict) else kwargs
    items = _require_list(effective_state, "items")
    contents = _metadata_by_index(_require_list(effective_state, "contents"))
    if len(contents) != len(items):
        raise ValueError(
            f"metadata count {len(contents)} does not match item count {len(items)}"
        )
    return {"extraction_complete": True}
