"""CAP journey census — LLM-free reduce (discover/extract live in extract.py).

Research plan: docs/2026-09-05-research-plan-cap-journey-census.md.
The reducer validates model claims against the catalog and the mechanical
facts: demote-never-drop (contested rows stay rows), evidence substring
check, canary gate after artifacts are written so raw rows stay readable.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.demos.cap_journey_census.extract import (  # noqa: E402
    cap_discover,
    cap_extract,
)

__all__ = ["cap_discover", "cap_extract", "reduce_cap_ledger"]

PROMPT_VERSION = "judge_cap.v1"
BLAST_KINDS = frozenset(
    {
        "core_runtime",
        "node_type",
        "cli_surface",
        "tooling_integration",
        "process_infra",
        "example_only",
    }
)
DISPOSITIONS = frozenset({"keep", "retire", "extend", "already_retired"})
_OFF_CATALOG = re.compile(r"^off_catalog:[a-z0-9_]{2,40}$")


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


# ------------------------------------------------------------------ reduce
class CapRow(BaseModel):
    item_ref: str
    cap_id: str
    name: str
    status: str
    source_index: int = Field(ge=0)
    classification_status: Literal["judged", "row_failed", "abstained"]
    journeys: list[str] = []
    off_catalog: list[str] = []
    blast_kind: str | None = None
    disposition: str | None = None
    disposition_effective: str | None = None
    anchor_violations: list[str] = []
    extend_to: str | None = None
    value_for_whom: str | None = None
    value_pain: str | None = None
    value_versus: str | None = None
    value_status: Literal["stated", "value_unstated"] | None = None
    consumer_cited: str | None = None
    evidence_span: str | None = None
    mechanical: dict[str, Any]
    failure_reason: str | None = None
    raw_finding: str | None = None
    model: str
    prompt_version: str = PROMPT_VERSION


# Path-based tool loading does not register the module for postponed annotation
# lookup, so rebuild while the module globals are still available.
CapRow.model_rebuild()


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _load_catalog(path: str) -> list[str]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    ids = [str(j["id"]) for j in data.get("journeys", [])]
    if not ids:
        raise ValueError("journey catalog is empty")
    return ids


def _bundles(contents: list[Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for pos, entry in enumerate(contents):
        idx, raw = (
            (entry.get("_map_index", pos), entry["value"])
            if isinstance(entry, dict) and "value" in entry
            else (pos, entry)
        )
        out[int(idx)] = json.loads(raw) if isinstance(raw, str) else raw
    return out


def _validate(
    verdict: dict[str, Any], bundle: dict[str, Any], catalog: list[str]
) -> tuple[dict[str, Any], str | None]:
    """Return (fields, fatal_reason). Anchor violations demote, never drop."""
    f: dict[str, Any] = {"anchor_violations": [], "off_catalog": []}
    journeys = verdict.get("journeys")
    if not isinstance(journeys, list) or not 1 <= len(journeys) <= 3:
        return f, "journeys must be a list of 1..3"
    clean: list[str] = []
    for j in journeys:
        j = str(j).strip()
        if j in catalog:
            clean.append(j)
        elif _OFF_CATALOG.match(j):
            f["off_catalog"].append(j.split(":", 1)[1])
        else:
            return f, f"journey {j!r} neither in catalog nor off_catalog:<label>"
    f["journeys"] = clean
    bk = str(verdict.get("blast_kind", "")).strip()
    if bk not in BLAST_KINDS:
        return f, f"blast_kind {bk!r} not in enum"
    f["blast_kind"] = bk
    disp = str(verdict.get("disposition", "")).strip()
    if disp not in DISPOSITIONS:
        return f, f"disposition {disp!r} not in enum"
    f["disposition"] = disp
    mech = bundle["mechanical"]
    all_consumers = set(mech["consumers_by_id"]) | set(mech["consumers_by_module"])
    cited = str(verdict.get("consumer_cited") or "").strip()
    f["consumer_cited"] = cited or None
    retired = bundle.get("status") == "retired"
    if disp == "keep" and not any(cited and cited in c for c in all_consumers):
        f["anchor_violations"].append(
            "keep without a consumer from the mechanical list"
        )
    if disp == "retire" and mech["consumer_count"] > 0:
        f["anchor_violations"].append(
            f"retire with {mech['consumer_count']} mechanical consumers"
        )
    if disp == "already_retired" and not retired:
        f["anchor_violations"].append("already_retired but CAP status is not retired")
    if retired and disp != "already_retired":
        f["anchor_violations"].append("CAP status retired but disposition differs")
    ext = str(verdict.get("extend_to") or "").strip()
    if disp == "extend":
        if ext not in catalog:
            f["anchor_violations"].append(f"extend_to {ext!r} not in catalog")
        f["extend_to"] = ext or None
    f["disposition_effective"] = disp if not f["anchor_violations"] else "contested"
    fw, vp, vv = (
        str(verdict.get(k) or "").strip()
        for k in ("value_for_whom", "value_pain", "value_versus")
    )
    f.update(value_for_whom=fw or None, value_pain=vp or None, value_versus=vv or None)
    f["value_status"] = "stated" if fw in catalog and vp and vv else "value_unstated"
    ev = str(verdict.get("evidence_span") or "").strip()
    # YAML folded scalars join lines with spaces; compare whitespace-normalized text.
    haystack = _squash(
        (bundle.get("cap_yaml") or "") + "\n" + (bundle.get("fr_head") or "")
    )
    if not ev or _squash(ev) not in haystack:
        return f, "evidence_span is not a substring of the CAP yaml or FR head"
    f["evidence_span"] = ev[:200]
    return f, None


def _row(
    bundle: dict[str, Any],
    index: int,
    model: str,
    status: str,
    fields: dict[str, Any],
    reason: str | None,
    raw: str | None,
) -> CapRow:
    return CapRow(
        item_ref=bundle["item_ref"],
        cap_id=str(bundle.get("id")),
        name=str(bundle.get("name")),
        status=str(bundle.get("status")),
        source_index=index,
        classification_status=status,  # type: ignore[arg-type]
        mechanical=bundle["mechanical"],
        failure_reason=(reason or None) and reason[:240],
        raw_finding=(raw or None) and raw[:2000],
        model=model,
        **fields,
    )


def _canary_gate(path: str | None, rows: list[CapRow]) -> list[str]:
    if not path:
        return []
    spec = yaml.safe_load(Path(path).read_text(encoding="utf-8")).get("canaries", [])
    by_cap = {r.cap_id: r for r in rows}
    misses: list[str] = []
    for c in spec:
        r = by_cap.get(c["cap"])
        if r is None:
            misses.append(f"{c['cap']}: absent from ledger")
            continue
        if r.classification_status != "judged":
            misses.append(f"{c['cap']}: {r.classification_status} ({r.failure_reason})")
            continue
        if not set(c.get("journeys_any", [])) & set(r.journeys):
            misses.append(f"{c['cap']}: journeys {r.journeys} miss {c['journeys_any']}")
        if r.disposition != c["disposition"]:
            misses.append(
                f"{c['cap']}: disposition {r.disposition} != {c['disposition']}"
            )
        if c.get("extend_to_any") and r.extend_to not in c["extend_to_any"]:
            misses.append(
                f"{c['cap']}: extend_to {r.extend_to} not in {c['extend_to_any']}"
            )
        if c.get("consumer_any") and not any(
            s in (r.consumer_cited or "") for s in c["consumer_any"]
        ):
            misses.append(
                f"{c['cap']}: consumer_cited {r.consumer_cited!r} misses {c['consumer_any']}"
            )
        blast = " ".join(
            r.mechanical.get("consumers_by_module", [])
            + r.mechanical.get("req_ids", [])
        )
        for bad in c.get("blast_excludes", []):
            if bad in blast:
                misses.append(f"{c['cap']}: blast contains excluded {bad!r}")
    return misses


def _mermaid(rows: list[CapRow]) -> str:
    lines = ["```mermaid", "graph LR"]
    for r in rows:
        for m in r.mechanical.get("consumers_by_module", [])[:5]:
            lines.append(
                f'  {r.cap_id}["{r.cap_id} {r.name[:28]}"] --> m{abs(hash(m)) % 10**6}["{m}"]'
            )
    lines.append("```")
    return "\n".join(lines) if len(lines) > 3 else "_no module consumers recorded_"


def _markdown(
    rows: list[CapRow], catalog: list[str], misses: list[str], meta: dict[str, Any]
) -> str:
    judged = [r for r in rows if r.classification_status == "judged"]
    out = [
        "# CAP Journey Census Ledger\n",
        f"- rows: {len(rows)}  judged: {len(judged)}  row_failed: {sum(r.classification_status == 'row_failed' for r in rows)}  abstained: {sum(r.classification_status == 'abstained' for r in rows)}",
        f"- model: {meta['model']}  git_sha: {meta['git_sha']}  prompt: {PROMPT_VERSION}",
        f"- canary misses: {len(misses)}"
        + (" — " + "; ".join(misses) if misses else ""),
        "",
    ]
    out.append(
        "## Journey × CAP matrix\n\n| journey | CAPs | keep | extend | retire | contested |\n|---|---:|---:|---:|---:|---:|"
    )
    for j in catalog:
        js = [r for r in judged if j in r.journeys]
        d = Counter(r.disposition_effective for r in js)
        out.append(
            f"| {j} | {len(js)} | {d['keep']} | {d['extend']} | {d['retire']} | {d['contested']} |"
        )
    off = Counter(o for r in judged for o in r.off_catalog)
    out.append(f"\noff-catalog labels: {dict(off) or 'none'}\n")
    out.append(
        "## Disposition table\n\n| CAP | name | disposition | effective | extend_to | consumer_cited | anchor violations |\n|---|---|---|---|---|---|---|"
    )
    for r in sorted(judged, key=lambda r: (r.disposition_effective or "", r.cap_id)):
        out.append(
            f"| {r.cap_id} | {r.name[:40]} | {r.disposition} | {r.disposition_effective} | {r.extend_to or '-'} | {r.consumer_cited or '-'} | {'; '.join(r.anchor_violations) or '-'} |"
        )
    out.append("\n## Value\n")
    out.append(
        f"value_unstated: {sum(r.value_status == 'value_unstated' for r in judged)} / {len(judged)}\n"
    )
    out.append("| CAP | for whom | pain | versus |\n|---|---|---|---|")
    for r in judged:
        out.append(
            f"| {r.cap_id} | {r.value_for_whom or '-'} | {(r.value_pain or '-')[:90]} | {(r.value_versus or '-')[:60]} |"
        )
    out.append("\n## Blast by journey\n")
    by_j: dict[str, list[CapRow]] = defaultdict(list)
    for r in judged:
        for j in r.journeys:
            by_j[j].append(r)
    for j in catalog:
        if by_j.get(j):
            out.append(f"### {j}\n\n{_mermaid(by_j[j])}\n")
    out.append("## Failed / abstained rows\n\n| CAP | status | reason |\n|---|---|---|")
    for r in rows:
        if r.classification_status != "judged":
            out.append(
                f"| {r.cap_id} | {r.classification_status} | {(r.failure_reason or '-')[:160]} |"
            )
    return "\n".join(out) + "\n"


def reduce_cap_ledger(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    state = state or {}
    items = state.get("items") or []
    contents = state.get("contents") or []
    findings = state.get("findings") or []
    output_path = _require(state, "output_path")
    catalog = _load_catalog(state.get("journeys_path") or str(HERE / "journeys.yaml"))
    model = str(state.get("model") or "unknown")
    if len(items) != len(contents):
        raise ValueError(
            f"items/contents length mismatch: {len(items)} vs {len(contents)}"
        )
    bundles = _bundles(contents)
    if set(bundles) != set(range(len(items))):
        raise ValueError("extracted bundles missing indices")
    rows: list[CapRow] = []
    seen: set[int] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("finding must be a dict")
        idx = finding.get("source_index", finding.get("_map_index"))
        if not isinstance(idx, int) or not 0 <= idx < len(items):
            raise ValueError(f"dangling finding index {idx!r}")
        if idx in seen:
            raise ValueError(f"duplicate finding for index {idx}")
        seen.add(idx)
        b = bundles[idx]
        if "_error" in finding:
            rows.append(
                _row(
                    b,
                    idx,
                    model,
                    "row_failed",
                    {},
                    f"map error: {finding['_error']}",
                    json.dumps(finding, sort_keys=True),
                )
            )
            continue
        verdict = finding.get("value") if "value" in finding else finding
        if not isinstance(verdict, dict):
            raise ValueError(f"finding {idx} value is not a dict")
        if verdict.get("abstained"):
            rows.append(
                _row(
                    b,
                    idx,
                    model,
                    "abstained",
                    {},
                    str(verdict.get("abstain_reason") or "abstained"),
                    json.dumps(verdict, sort_keys=True),
                )
            )
            continue
        fields, fatal = _validate(verdict, b, catalog)
        if fatal:
            rows.append(
                _row(
                    b,
                    idx,
                    model,
                    "row_failed",
                    {},
                    fatal,
                    json.dumps(verdict, sort_keys=True),
                )
            )
        else:
            rows.append(_row(b, idx, model, "judged", fields, None, None))
    missing = set(range(len(items))) - seen
    if missing:
        raise ValueError(f"missing findings for indices: {sorted(missing)}")
    rows.sort(key=lambda r: r.source_index)

    sha = (
        subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        or "unknown"
    )
    meta = {
        "model": model,
        "git_sha": sha,
        "collected_at": datetime.now(UTC).isoformat(),
        "rows": len(rows),
    }
    misses = _canary_gate(state.get("canaries_path") or None, rows)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    jsonl = out.with_suffix(".jsonl")
    jsonl.write_text(
        "".join(r.model_dump_json() + "\n" for r in rows), encoding="utf-8"
    )
    out.write_text(_markdown(rows, catalog, misses, meta), encoding="utf-8")
    meta["ledger_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    meta["canary_misses"] = misses
    out.with_suffix(".run.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    if misses:
        raise ValueError(
            f"canary gate failed ({len(misses)}); raw rows at {jsonl}: "
            + "; ".join(misses)
        )
    return {"ledger": {"output_path": str(out), "jsonl_path": str(jsonl), "run": meta}}
