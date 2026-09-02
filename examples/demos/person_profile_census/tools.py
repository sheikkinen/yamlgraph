"""FR-962 person-profile census: preflight + LLM-free fail-closed PR reducer.

- `preflight` enforces Azure env + visibility BEFORE any gh call.
- `PRLedgerRow` is the frozen row schema (R-2 shape).
- `reduce_pr_ledger` re-implements attribution + containment locally
  (R-3: NOT auto-inherited from FR-943), computes mechanical rollups,
  enforces the typed hidden canary (R-4), and writes markdown + JSONL.
- `prepare_brief_input` selects a URL-bearing bounded input for FR-895
  synthesis; `render_brief` validates PR URL citations.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, ValidationError

AZURE_VARS = ("AZURE_AI_ENDPOINT", "AZURE_AI_API_KEY", "AZURE_MODEL")
VALID_VISIBILITY = {"public", "private", "internal"}
CHANGE_KIND_ENUM = frozenset(
    {"feat", "fix", "docs", "refactor", "chore", "infra", "ops", "test", "revert"}
)
MAX_LABELS = 10
MAX_INTENT_CHARS = 280
MAX_SURFACES = 5
MAX_FAILURE_REASON = 240
BRIEF_TOP_N = 30
PROMPT_VERSION = "classify_pr.v1"
SYNTH_PROMPT_VERSION = "synthesize_person_brief.v1"

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _parse_json_list(raw: Any, name: str) -> list[str]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name} must be a JSON list, got {raw!r}") from exc
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{name} must be a non-empty list")
    seen: set[str] = set()
    canonical: list[str] = []
    for entry in raw:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{name} entries must be non-empty strings; got {entry!r}")
        key = entry.casefold()
        if key in seen:
            raise ValueError(
                f"{name} entries must be unique under casefold; dup: {entry!r}"
            )
        seen.add(key)
        canonical.append(entry)
    return canonical


def preflight(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Azure + visibility preflight (R-5) — fail BEFORE any gh call."""
    state = state or {}
    missing_env = [v for v in AZURE_VARS if not os.environ.get(v, "").strip()]
    if missing_env:
        raise ValueError(
            "azure preflight failed, refusing to discover: "
            f"missing env {', '.join(missing_env)}"
        )
    visibility = _parse_json_list(state.get("visibility"), "visibility")
    for entry in visibility:
        if entry.casefold() not in VALID_VISIBILITY:
            raise ValueError(
                f"visibility preflight: unknown value {entry!r}; "
                f"allowed {sorted(VALID_VISIBILITY)}"
            )
    if not state.get("azure_model", "").strip():
        raise ValueError("preflight: azure_model state var is required")
    return {"preflight_ok": True}


def preflight_smoke(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Smoke-only preflight — visibility check without Azure env.
    NEVER commit a graph that uses this; committed graph uses `preflight`.
    """
    state = state or {}
    visibility = _parse_json_list(state.get("visibility"), "visibility")
    for entry in visibility:
        if entry.casefold() not in VALID_VISIBILITY:
            raise ValueError(
                f"visibility preflight (smoke): unknown value {entry!r}; "
                f"allowed {sorted(VALID_VISIBILITY)}"
            )
    return {"preflight_ok": True}


class PRLedgerRow(BaseModel):
    """FR-962 person-profile census ledger row (R-2 + R-3)."""

    item_ref: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    number: int = Field(gt=0)
    url: HttpUrl
    title: str
    state: Literal["open", "closed", "merged"]
    created_at: str = Field(min_length=1)
    merged_at: str | None
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    changed_files: int = Field(ge=0)
    labels: list[str] = Field(max_length=MAX_LABELS)
    base_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    classification_status: Literal["judged", "row_failed"]
    problem_class: str | None
    change_kind: (
        Literal[
            "feat", "fix", "docs", "refactor", "chore", "infra", "ops", "test", "revert"
        ]
        | None
    )
    surfaces: list[str] | None
    intent: str | None
    evidence_citation: str | None
    failure_reason: str | None
    raw_finding: str | None
    model: str
    prompt_version: str
    source_index: int = Field(ge=0)


PRLedgerRow.model_rebuild()  # resolve HttpUrl forward ref under `from __future__ import annotations`


def _blob_by_index(contents: list[Any]) -> dict[int, dict[str, Any]]:
    """Return {source_index: PR bundle dict}, mirroring FR-899 shape."""
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


def _finding_index(finding: dict[str, Any], total: int) -> int:
    index = finding.get("source_index")
    if index is None:
        index = finding.get("_map_index")
    if not isinstance(index, int):
        raise ValueError("finding missing source index")
    if index < 0 or index >= total:
        raise ValueError(f"dangling: finding index {index} out of range")
    return index


def _canonical(value: str, allowed: list[str]) -> str | None:
    key = value.casefold()
    for entry in allowed:
        if entry.casefold() == key:
            return entry
    return None


def _row_failed(
    item_ref: str,
    blob: dict[str, Any],
    reason: str,
    raw_finding: str,
    model: str,
    source_index: int,
) -> PRLedgerRow:
    return PRLedgerRow(
        item_ref=item_ref,
        repo=blob["repo"],
        number=blob["number"],
        url=blob["url"],
        title=blob["title"],
        state=blob["state"],
        created_at=blob["created_at"],
        merged_at=blob.get("merged_at"),
        additions=blob["additions"],
        deletions=blob["deletions"],
        changed_files=blob["changed_files"],
        labels=blob["labels"],
        base_sha=blob["base_sha"],
        head_sha=blob["head_sha"],
        classification_status="row_failed",
        problem_class=None,
        change_kind=None,
        surfaces=None,
        intent=None,
        evidence_citation=None,
        failure_reason=reason[:MAX_FAILURE_REASON],
        raw_finding=raw_finding[:2000],
        model=model,
        prompt_version=PROMPT_VERSION,
        source_index=source_index,
    )


def _judged_row(
    item_ref: str,
    blob: dict[str, Any],
    verdict: dict[str, Any],
    problem_labels: list[str],
    surface_labels: list[str],
    model: str,
    source_index: int,
) -> tuple[PRLedgerRow | None, str | None]:
    """Return (row, error). error non-None => caller emits row_failed."""
    pc_raw = verdict.get("problem_class")
    if not isinstance(pc_raw, str) or not pc_raw.strip():
        return None, "empty problem_class"
    pc = _canonical(pc_raw.strip(), problem_labels)
    if pc is None:
        return None, f"problem_class {pc_raw!r} not in vocabulary"

    ck_raw = verdict.get("change_kind")
    if not isinstance(ck_raw, str) or ck_raw.strip().casefold() not in CHANGE_KIND_ENUM:
        return None, f"change_kind {ck_raw!r} not in enum"
    ck = ck_raw.strip().casefold()

    surfaces_raw = verdict.get("surfaces")
    if not isinstance(surfaces_raw, list) or not (
        1 <= len(surfaces_raw) <= MAX_SURFACES
    ):
        return None, f"surfaces must be 1..{MAX_SURFACES} entries"
    surfaces: list[str] = []
    seen_surface: set[str] = set()
    for s in surfaces_raw:
        if not isinstance(s, str) or not s.strip():
            return None, "surfaces entries must be non-empty strings"
        canon = _canonical(s.strip(), surface_labels)
        if canon is None:
            return None, f"surface {s!r} not in vocabulary"
        if canon.casefold() in seen_surface:
            return None, f"duplicate surface {canon!r}"
        seen_surface.add(canon.casefold())
        surfaces.append(canon)

    intent = verdict.get("intent")
    if not isinstance(intent, str) or not intent.strip():
        return None, "empty intent"
    intent = intent.strip()
    if "\n" in intent or len(intent) > MAX_INTENT_CHARS:
        return None, f"intent must be <= {MAX_INTENT_CHARS} single-line chars"

    evidence = verdict.get("evidence_span")
    if not isinstance(evidence, str) or not evidence.strip():
        return None, "empty evidence_span"
    body = blob.get("body_head") or ""
    title = blob.get("title") or ""
    if evidence not in title and evidence not in body:
        return None, "evidence_span is not a substring of title or body"

    try:
        row = PRLedgerRow(
            item_ref=item_ref,
            repo=blob["repo"],
            number=blob["number"],
            url=blob["url"],
            title=blob["title"],
            state=blob["state"],
            created_at=blob["created_at"],
            merged_at=blob.get("merged_at"),
            additions=blob["additions"],
            deletions=blob["deletions"],
            changed_files=blob["changed_files"],
            labels=blob["labels"],
            base_sha=blob["base_sha"],
            head_sha=blob["head_sha"],
            classification_status="judged",
            problem_class=pc,
            change_kind=ck,  # type: ignore[arg-type]
            surfaces=surfaces,
            intent=intent,
            evidence_citation=f"{item_ref}::{evidence[:120]}",
            failure_reason=None,
            raw_finding=None,
            model=model,
            prompt_version=PROMPT_VERSION,
            source_index=source_index,
        )
    except ValidationError as exc:
        return None, f"row validation: {exc.errors()[0]['msg']}"
    return row, None


def _mechanical_rollup(rows: list[PRLedgerRow]) -> dict[str, Any]:
    from collections import Counter

    repos = Counter(r.repo for r in rows)
    labels = Counter(lbl for r in rows for lbl in r.labels)
    merged = sum(1 for r in rows if r.state == "merged")
    judged = [r for r in rows if r.classification_status == "judged"]
    kinds = Counter(r.change_kind for r in judged)
    problem = Counter(r.problem_class for r in judged)
    surfaces = Counter(s for r in judged if r.surfaces for s in r.surfaces)
    dates = [r.created_at for r in rows if r.created_at]
    months: Counter[str] = Counter()
    for d in dates:
        if len(d) >= 7 and d[4] == "-":
            months[d[:7]] += 1
    top_by_size = sorted(
        rows,
        key=lambda r: (r.additions + r.deletions),
        reverse=True,
    )[:10]
    return {
        "total_prs": len(rows),
        "repos": dict(repos.most_common()),
        "timespan": {
            "min": min(dates) if dates else None,
            "max": max(dates) if dates else None,
        },
        "merge_rate": (merged / len(rows)) if rows else 0.0,
        "monthly_cadence": dict(sorted(months.items())),
        "label_histogram": dict(labels.most_common()),
        "change_kind_histogram": dict(kinds.most_common()),
        "surfaces_histogram": dict(surfaces.most_common()),
        "problem_class_histogram": dict(problem.most_common()),
        "top_by_size": [
            {
                "item_ref": r.item_ref,
                "url": str(r.url),
                "delta": r.additions + r.deletions,
                "title": r.title,
            }
            for r in top_by_size
        ],
        "classification_coverage": (len(judged) / len(rows)) if rows else 0.0,
    }


def _family_match(judged_surfaces: list[str] | None, family: list[str]) -> bool:
    if not judged_surfaces:
        return False
    j = {s.casefold() for s in judged_surfaces}
    for f in family:
        fk = f.casefold()
        for js in j:
            if fk in js or js in fk:
                return True
    return False


def _canary_gate(canary: Any, rows: list[PRLedgerRow]) -> None:
    if not canary:
        return  # optional in smoke; enforce path passes a real one
    if isinstance(canary, str):
        canary = json.loads(canary)
    if not isinstance(canary, dict):
        raise ValueError("canary must be a dict")
    item_ref = canary.get("item_ref")
    family = canary.get("surface_family")
    if not isinstance(item_ref, str) or not item_ref:
        raise ValueError("canary.item_ref required")
    if not isinstance(family, list) or not family:
        raise ValueError("canary.surface_family required")
    match = next((r for r in rows if r.item_ref == item_ref), None)
    if match is None:
        raise ValueError(f"canary: item {item_ref} absent from ledger")
    if match.classification_status == "row_failed":
        raise ValueError(f"canary: item {item_ref} row_failed")
    if not _family_match(match.surfaces, [str(f) for f in family]):
        raise ValueError(
            f"canary: item {item_ref} surfaces {match.surfaces} miss family {family}"
        )


def reduce_pr_ledger(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    state = state or {}
    items = state.get("items") or []
    contents = state.get("contents") or []
    findings = state.get("findings") or []
    problem_labels = _parse_json_list(state.get("problem_labels"), "problem_labels")
    surface_labels = _parse_json_list(state.get("surface_labels"), "surface_labels")
    output_path = state.get("output_path")
    if not isinstance(output_path, str) or not output_path:
        raise ValueError("output_path required")
    azure_model = state.get("azure_model") or os.environ.get("AZURE_MODEL", "unknown")

    if len(items) != len(contents):
        raise ValueError(
            f"items/contents length mismatch: {len(items)} vs {len(contents)}"
        )
    blobs = _blob_by_index(contents)
    if set(blobs.keys()) != set(range(len(items))):
        raise ValueError("extracted bundles missing indices")

    rows: list[PRLedgerRow] = []
    seen_index: set[int] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("finding must be a dict")
        index = _finding_index(finding, len(items))
        if index in seen_index:
            raise ValueError(f"duplicate finding for index {index}")
        seen_index.add(index)
        item_ref = items[index]
        blob = blobs[index]

        if "_error" in finding:
            rows.append(
                _row_failed(
                    item_ref,
                    blob,
                    f"map error: {finding['_error']}",
                    json.dumps(finding, sort_keys=True),
                    azure_model,
                    index,
                )
            )
            continue

        verdict = finding.get("value") if "value" in finding else finding
        if not isinstance(verdict, dict):
            raise ValueError(f"finding {index} value is not a dict")

        row, err = _judged_row(
            item_ref, blob, verdict, problem_labels, surface_labels, azure_model, index
        )
        if err is not None:
            rows.append(
                _row_failed(
                    item_ref,
                    blob,
                    err,
                    json.dumps(verdict, sort_keys=True),
                    azure_model,
                    index,
                )
            )
        else:
            assert row is not None
            rows.append(row)

    if len(rows) != len(items):
        missing = set(range(len(items))) - {r.source_index for r in rows}
        raise ValueError(f"missing findings for indices: {sorted(missing)}")

    rollup = _mechanical_rollup(rows)
    _canary_gate(state.get("canary"), rows)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = out.with_suffix(".jsonl")
    meta_path = out.with_suffix(".run.json")

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(r.model_dump_json() + "\n")

    md_lines: list[str] = []
    md_lines.append("# Person Profile Census Ledger\n")
    md_lines.append(
        f"Source: `{state.get('source', '')}`  visibility: `{state.get('visibility', '')}`\n\n"
    )
    md_lines.append("## Mechanical rollup\n")
    md_lines.append(f"- total PRs: {rollup['total_prs']}\n")
    md_lines.append(
        f"- timespan: {rollup['timespan']['min']} → {rollup['timespan']['max']}\n"
    )
    md_lines.append(f"- merge rate: {rollup['merge_rate']:.1%}\n")
    md_lines.append(
        f"- classification coverage: {rollup['classification_coverage']:.1%}\n\n"
    )

    def _hist_table(name: str, hist: dict[str, int]) -> list[str]:
        if not hist:
            return []
        rows_out = [f"### {name}\n\n| value | count |\n|---|---|\n"]
        rows_out.extend(f"| {k} | {v} |\n" for k, v in hist.items())
        rows_out.append("\n")
        return rows_out

    md_lines.extend(_hist_table("Repos", rollup["repos"]))
    md_lines.extend(_hist_table("change_kind", rollup["change_kind_histogram"]))
    md_lines.extend(_hist_table("surfaces", rollup["surfaces_histogram"]))
    md_lines.extend(_hist_table("problem_class", rollup["problem_class_histogram"]))
    md_lines.extend(_hist_table("monthly cadence", rollup["monthly_cadence"]))

    md_lines.append("## Top by size\n\n")
    for t in rollup["top_by_size"]:
        md_lines.append(
            f"- [{t['item_ref']}]({t['url']}) ±{t['delta']} — {t['title']}\n"
        )
    md_lines.append("\n## Per-PR rows\n\n")
    md_lines.append("| item_ref | change_kind | problem_class | surfaces | intent |\n")
    md_lines.append("|---|---|---|---|---|\n")
    for r in rows:
        surfaces = ", ".join(r.surfaces) if r.surfaces else "-"
        md_lines.append(
            f"| [{r.item_ref}]({r.url}) | {r.change_kind or 'ROW_FAILED'} "
            f"| {r.problem_class or '-'} | {surfaces} "
            f"| {(r.intent or r.failure_reason or '-')[:120]} |\n"
        )
    out.write_text("".join(md_lines), encoding="utf-8")

    ledger_hash = hashlib.sha256(out.read_bytes()).hexdigest()
    run_metadata = {
        "run_id": str(uuid.uuid4()),
        "collected_at": datetime.now(UTC).isoformat(),
        "source": state.get("source"),
        "visibility": state.get("visibility"),
        "discovered": len(items),
        "classified": sum(1 for r in rows if r.classification_status == "judged"),
        "row_failed": sum(1 for r in rows if r.classification_status == "row_failed"),
        "map_calls": len(items),
        "azure_model": azure_model,
        "prompt_version": PROMPT_VERSION,
        "synthesis_prompt_version": SYNTH_PROMPT_VERSION,
        "ledger_sha256": ledger_hash,
    }
    meta_path.write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")

    return {
        "ledger": {
            "output_path": str(out),
            "jsonl_path": str(jsonl_path),
            "meta_path": str(meta_path),
            "rollup": rollup,
            "row_count": len(rows),
            "run_metadata": run_metadata,
        }
    }


def prepare_brief_input(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    state = state or {}
    ledger = state.get("ledger") or {}
    jsonl_path = ledger.get("jsonl_path")
    if not jsonl_path:
        raise ValueError("ledger.jsonl_path required")
    rows: list[dict[str, Any]] = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("classification_status") != "judged":
                continue
            rows.append(
                {
                    "url": row["url"],
                    "repo": row["repo"],
                    "number": row["number"],
                    "title": row["title"],
                    "problem_class": row["problem_class"],
                    "change_kind": row["change_kind"],
                    "surfaces": row["surfaces"],
                    "intent": row["intent"],
                    "delta": row["additions"] + row["deletions"],
                    "state": row["state"],
                }
            )
    rows.sort(key=lambda r: r["delta"], reverse=True)
    return {"brief_input": rows[:BRIEF_TOP_N]}


def _claims_to_markdown(claims: dict[str, Any], url_titles: dict[str, str]) -> str:
    """Render PersonProfileBriefClaims (schema) as markdown."""
    lines: list[str] = []
    title = claims.get("title") or "Person profile"
    lines.append(f"# {title}\n")
    lines.append("## Themes\n")
    for theme in claims.get("themes") or []:
        if not isinstance(theme, dict):
            continue
        lines.append(f"### {theme.get('theme', '')}\n")
        evidence = theme.get("evidence", "")
        if evidence:
            lines.append(f"{evidence}\n")
        for url in theme.get("pr_urls") or []:
            label = url_titles.get(url, url)
            lines.append(f"- [{label}]({url})")
        lines.append("")
    if surf := claims.get("surface_concentration"):
        lines.append(f"## Surface concentration\n\n{surf}\n")
    if cad := claims.get("cadence"):
        lines.append(f"## Cadence\n\n{cad}\n")
    lines.append("## Notable PRs\n")
    for pr in claims.get("notable_prs") or []:
        if not isinstance(pr, dict):
            continue
        url = pr.get("url", "")
        pr_title = pr.get("title") or url_titles.get(url, url)
        lines.append(f"### [{pr_title}]({url})")
        if reason := pr.get("reason"):
            lines.append(f"\n**Why:** {reason}")
        if evidence := pr.get("evidence"):
            lines.append(f"\n**Evidence:** {evidence}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_brief(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    state = state or {}
    brief_path = state.get("brief_path")
    if not isinstance(brief_path, str) or not brief_path:
        raise ValueError("brief_path required")
    claims = state.get("claims") or {}
    brief_input = state.get("brief_input") or []
    allowed_urls = {r["url"] for r in brief_input}
    url_titles = {r["url"]: r["title"] for r in brief_input}

    body = (
        claims.get("output")
        if isinstance(claims, dict) and "output" in claims
        else claims
    )

    # Citation-boundary URL scan runs on whatever the LLM emitted, string or dict.
    scan_text = body if isinstance(body, str) else json.dumps(body)
    fabricated: list[str] = []
    for token in scan_text.replace(",", " ").replace('"', " ").split():
        if token.startswith("https://github.com/") and "/pull/" in token:
            cleaned = token.rstrip(").,;\"'")
            if cleaned not in allowed_urls:
                fabricated.append(cleaned)

    if isinstance(body, dict):
        text = _claims_to_markdown(body, url_titles)
    elif isinstance(body, str):
        text = body
    else:
        text = json.dumps(body, indent=2)

    out = Path(brief_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    claims_path = out.with_suffix(".claims.json")
    claims_path.write_text(
        json.dumps(body, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if fabricated:
        rejected = out.with_suffix(".REJECTED.md")
        rejected.write_text(
            "# Brief REJECTED — fabricated PR URLs\n\n"
            f"Fabricated: {sorted(set(fabricated))}\n\n---\n\n{text}\n",
            encoding="utf-8",
        )
        return {
            "brief": {
                "brief_path": None,
                "claims_path": str(claims_path),
                "rejected_path": str(rejected),
                "fabricated": sorted(set(fabricated)),
            }
        }
    out.write_text(text, encoding="utf-8")
    return {
        "brief": {
            "brief_path": str(out),
            "claims_path": str(claims_path),
            "accepted": True,
        }
    }
