"""FR-899 org repo census: Azure preflight and LLM-free fail-closed reducer.

Activity and persons are code-owned (C-4): activity derives mechanically
from the extracted API fields, persons are copied verbatim from the
contributor API data. The LLM contributes only the purpose judgement.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

PUBLIC_DEMO_ORG = "sheikkinen"
AZURE_VARS = ("AZURE_AI_ENDPOINT", "AZURE_AI_API_KEY", "AZURE_MODEL")
DEFAULT_ACTIVITY_WINDOW_DAYS = 180
MAX_PERSONS = 5
PROMPT_VERSION = "judge_repo_purpose.v1"
SYNTHESIS_PROMPT_VERSION = "synthesize_repo_brief.v1"

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def preflight(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Fail loudly BEFORE any gh discovery when Azure pinning is unconfigured."""
    missing = [var for var in AZURE_VARS if not os.environ.get(var, "").strip()]
    if missing:
        raise ValueError(
            "azure preflight failed, refusing to discover corp data: "
            f"missing {', '.join(missing)}"
        )
    return {"preflight_ok": True}


class RepoLedgerRow(BaseModel):
    """One fail-closed repo census ledger row (FR-899 frozen schema)."""

    name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    persons: list[str]
    activity: Literal["active", "dormant", "archived"]
    evidence_citation: str = Field(min_length=1)
    model: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    source_index: int = Field(ge=0)


def _blob_by_index(contents: list[Any]) -> dict[int, dict[str, Any]]:
    blobs: dict[int, dict[str, Any]] = {}
    for position, entry in enumerate(contents):
        if isinstance(entry, dict) and "value" in entry:
            index = entry.get("_map_index", position)
            raw = entry["value"]
        else:
            index, raw = position, entry
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(parsed, dict):
            raise ValueError(f"extracted bundle {index} is not a JSON object")
        blobs[int(index)] = parsed
    return blobs


def _derive_activity(blob: dict[str, Any], window_days: int) -> str:
    if blob.get("archived") is True:
        return "archived"
    pushed_at = blob.get("pushed_at")
    if not isinstance(pushed_at, str) or not pushed_at.strip():
        raise ValueError(f"bundle for {blob.get('name')} lacks pushed_at")
    pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    age_days = (datetime.now(UTC) - pushed).total_seconds() / 86400
    return "active" if age_days <= window_days else "dormant"


def _persons_from(blob: dict[str, Any]) -> list[str]:
    contributors = blob.get("contributors")
    if not isinstance(contributors, list):
        raise ValueError(f"bundle for {blob.get('name')} lacks contributors")
    return [str(login) for login in contributors[:MAX_PERSONS]]


def _finding_index(finding: dict[str, Any], total: int) -> int:
    index = finding.get("source_index")
    if index is None:
        index = finding.get("_map_index")
    if not isinstance(index, int):
        raise ValueError("finding missing source index")
    if index < 0 or index >= total:
        raise ValueError(f"dangling citation: finding index {index} out of range")
    return index


def _build_rows(
    items: list[str],
    contents: list[Any],
    findings: list[dict[str, Any]],
    window_days: int,
) -> list[RepoLedgerRow]:
    blobs = _blob_by_index(contents)
    azure_model = os.environ.get("AZURE_MODEL", "azure")
    rows: list[RepoLedgerRow] = []
    seen: set[int] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("finding must be a dict")
        if "_error" in finding:
            raise ValueError(f"finding carries map error: {finding['_error']}")
        index = _finding_index(finding, len(items))
        if index in seen:
            raise ValueError(f"duplicate finding for repo index {index}")
        seen.add(index)

        blob = blobs.get(index)
        if blob is None:
            raise ValueError(f"no extracted bundle for repo index {index}")
        purpose = str(finding.get("purpose", "")).strip()
        span = str(finding.get("evidence_span", "")).strip()
        try:
            rows.append(
                RepoLedgerRow(
                    name=items[index],
                    purpose=purpose,
                    persons=_persons_from(blob),
                    activity=_derive_activity(blob, window_days),
                    evidence_citation=f"{items[index]}: {span}" if span else "",
                    model=azure_model,
                    prompt_version=PROMPT_VERSION,
                    source_index=index,
                )
            )
        except ValidationError as exc:
            raise ValueError(
                f"invalid repo ledger row for {items[index]}: {exc}"
            ) from exc

    unmatched = sorted(set(range(len(items))) - seen)
    if unmatched:
        raise ValueError(f"missing findings for repo indexes: {unmatched}")
    return sorted(rows, key=lambda row: row.name)


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()


def _emit_ledger(rows: list[RepoLedgerRow], output_path: str) -> dict[str, Any]:
    md_path = Path(output_path)
    if not md_path.suffix:
        md_path = md_path.with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = md_path.with_suffix(".jsonl")

    lines = [
        "# Org Repository Census Ledger",
        "",
        "| name | purpose | persons | activity | evidence_citation | model | prompt_version |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    _markdown_cell(row.name),
                    _markdown_cell(row.purpose),
                    _markdown_cell(", ".join(row.persons)),
                    row.activity,
                    _markdown_cell(row.evidence_citation),
                    _markdown_cell(row.model),
                    _markdown_cell(row.prompt_version),
                )
            )
            + " |"
        )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.model_dump(), sort_keys=True) + "\n")
    return {
        "markdown_path": str(md_path),
        "jsonl_path": str(jsonl_path),
        "rows": len(rows),
    }


def reduce_repo_ledger(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Join purpose findings with extracted bundles into the frozen ledger."""
    effective = state if isinstance(state, dict) else kwargs
    items = effective.get("items")
    contents = effective.get("contents")
    findings = effective.get("findings")
    output_path = effective.get("output_path")
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    if not isinstance(contents, list):
        raise ValueError("contents must be a list")
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("output_path must be a non-empty string")
    window_days = int(
        effective.get("activity_window_days") or DEFAULT_ACTIVITY_WINDOW_DAYS
    )
    rows = _build_rows([str(item) for item in items], contents, findings, window_days)
    return {"ledger": _emit_ledger(rows, output_path)}


def _required_var(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required variable: {key}")
    return value.strip()


def prepare_brief_input(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Map repo ledger rows into the FR-895 citation-boundary input shape."""
    from examples.demos.corpus_census.adapters import census_brief

    effective = state if isinstance(state, dict) else kwargs
    _required_var(effective, "brief_path")
    _required_var(effective, "brief_rubric")
    ledger = effective.get("ledger")
    if not isinstance(ledger, dict):
        raise ValueError("ledger must be a dict")
    jsonl_path = _required_var(ledger, "jsonl_path")

    mapped: list[dict[str, Any]] = []
    with Path(jsonl_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            mapped.append(
                {
                    "item_ref": row["name"],
                    "judgement": row["purpose"],
                    "label": f"{row['activity']}:{row['name']}",
                    "entries": 1,
                }
            )
    return {"brief_input": census_brief.build_synthesis_input(mapped)}


def render_brief(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Emit the corp brief through the FR-895 LLM-free citation boundary."""
    from examples.demos.corpus_census.adapters import census_brief

    effective = state if isinstance(state, dict) else kwargs
    brief_path = _required_var(effective, "brief_path")
    brief_input = effective.get("brief_input")
    if not isinstance(brief_input, list):
        raise ValueError("brief_input must be a list")
    claims_output = effective.get("claims")
    if not isinstance(claims_output, dict):
        raise ValueError("claims must be a dict")
    claims = claims_output.get("claims")
    if not isinstance(claims, list):
        raise ValueError("claims.claims must be a list")
    ledger = effective.get("ledger")
    if not isinstance(ledger, dict):
        raise ValueError("ledger must be a dict")

    result = census_brief.emit_brief(
        claims,
        brief_input,
        brief_path,
        run_meta={
            "model": os.environ.get("AZURE_MODEL", "azure"),
            "prompt_version": SYNTHESIS_PROMPT_VERSION,
            "rows": len(brief_input),
            "source_jsonl_path": _required_var(ledger, "jsonl_path"),
        },
    )
    return {"brief": result}
