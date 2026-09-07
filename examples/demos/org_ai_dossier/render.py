"""FR-1027 person input, summary boundary, findings input, atomic renderer.

Only `render_artifacts` writes files, and only after every claim passed the
citation boundary and the onepager passed its word/finding bounds; the output
directory appears atomically (temp dir + rename) so a failure leaves nothing.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from examples.demos.org_ai_dossier.docs import (
    _dossier,
    _jira_md,
    _onepager,
    _repos_md,
    _write_ledgers,
)
from examples.demos.org_ai_dossier.models import RunRecord

GRAPH_PATH = Path(__file__).resolve().parent / "graph.yaml"
PROMPT_VERSIONS = {
    "classify_repo_ai": "classify_repo_ai.v1",
    "classify_jira_ai": "classify_jira_ai.v1",
    "summarize_person": "summarize_person.v1",
    "synthesize_findings": "synthesize_findings.v1",
    "synthesize_onepager": "synthesize_onepager.v1",
}
BANNED_CLAIM_RE = re.compile(
    r"\b(senior|junior|lead(er)?ship|performance|underperform|overwork|workload|burn ?out|"
    r"lazy|productive|probably|intends?|wants? to|plans? to|feels?|frustrat|happy|unhappy|"
    r"better than|worse than|more than others|top performer)\b",
    re.IGNORECASE,
)
PERSON_ID_RE = re.compile(r"\b(github|jira):[^\s,.;]+")


def _head_sha() -> str:
    try:
        out = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _person_rows(reduced: dict[str, Any]) -> list[dict[str, Any]]:
    return list(reduced.get("persons_github", [])) + list(
        reduced.get("persons_jira", [])
    )


def prepare_person_input(state: dict[str, Any]) -> dict[str, Any]:
    """Source-qualified footprints for the summary map; routing flag for the graph."""
    active = str(state.get("persons_llm", "")).strip().lower() == "true"
    if not active:
        return {"person_input": [], "persons_llm_active": False}
    reduced = state["reduced"]
    purposes = reduced.get("purposes", {})
    rows = []
    for p in _person_rows(reduced):
        units = p["repos"] if p["source"] == "github" else p["projects"]
        rows.append(
            {
                "id": p["id"],
                "label": p["label"],
                "source": p["source"],
                "score": p["score"],
                "footprint": [{"id": u, "purpose": purposes.get(u, "")} for u in units],
            }
        )
    return {"person_input": rows, "persons_llm_active": True}


def _check_summary(
    summary: Any, person: dict[str, Any], all_ids: set[str], all_labels: set[str]
) -> str:
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError(f"summary for {person['id']} is empty")
    text = summary.strip()
    footprint = {u["id"] for u in person["footprint"]}
    # repo-shaped tokens must be footprint units; project keys known elsewhere are rejected too
    for token in re.findall(r"\b[\w.-]+/[\w.-]+\b", text):
        if token not in footprint:
            raise ValueError(
                f"summary for {person['id']} names repository {token} outside its footprint"
            )
    for token in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", text):
        if token in all_ids and token not in footprint:
            raise ValueError(
                f"summary for {person['id']} names project {token} outside its footprint"
            )
    for m in PERSON_ID_RE.findall(text):
        raise ValueError(
            f"summary for {person['id']} references another person id ({m})"
        )
    for label in all_labels - {person["label"]}:
        if label and re.search(rf"\b{re.escape(label)}\b", text):
            raise ValueError(
                f"summary for {person['id']} names another person ({label})"
            )
    hit = BANNED_CLAIM_RE.search(text)
    if hit:
        raise ValueError(
            f"summary for {person['id']} carries a banned claim ({hit.group(0)!r})"
        )
    return text


def prepare_findings_input(state: dict[str, Any]) -> dict[str, Any]:
    """Attach validated summaries; build the citable synthesis input."""
    reduced = json.loads(json.dumps(state["reduced"]))
    persons = _person_rows(reduced)
    if state.get("persons_llm_active"):
        person_input = state.get("person_input") or []
        summaries = {
            s.get("source_index", s.get("_map_index")): s
            for s in state.get("person_summaries") or []
        }
        all_ids = {r["id"] for r in reduced["repos"]} | {
            j["key"] for j in reduced["jira"]
        }
        all_labels = {p["label"] for p in persons}
        by_id = {p["id"]: p for p in persons}
        for i, pin in enumerate(person_input):
            if i not in summaries:
                raise ValueError(f"summary missing for {pin['id']}")
            by_id[pin["id"]]["summary"] = _check_summary(
                summaries[i].get("summary"), pin, all_ids, all_labels
            )
    rows = [
        {
            "item_ref": f"repo:{r['id']}",
            "judgement": r["purpose"],
            "label": f"{r['ai_usage']}:{r['id']}",
            "entries": 1 + len(r["ai_tools"]),
        }
        for r in reduced["repos"]
    ]
    rows += [
        {
            "item_ref": f"jira:{j['key']}",
            "judgement": j["purpose"],
            "label": f"{j['ai_usage']}:{j['key']}",
            "entries": 1 + len(j["ai_tools"]),
        }
        for j in reduced["jira"]
    ]
    rows += [
        {
            "item_ref": f"tool:{t['name']}",
            "judgement": t["kind"],
            "label": f"tool:{t['name']}",
            "entries": t["n_repos"] + t["n_projects"],
        }
        for t in reduced["ai_tools"]
    ]
    rows += [
        {
            "item_ref": f"person:{p['id']}",
            "judgement": p.get("summary") or "",
            "label": f"person:{p['id']}",
            "entries": p["score"],
        }
        for p in persons
    ]
    return {
        "reduced": reduced,
        "findings_input": {
            "rows": rows,
            "coverage": reduced["coverage"],
            "ai_tools": reduced["ai_tools"][:20],
        },
    }


# --- rendering -------------------------------------------------------------------


def _validate_claims(
    claims_obj: Any, rows: list[dict[str, Any]], label: str
) -> list[dict[str, Any]]:
    from examples.demos.corpus_census.adapters import census_brief

    claims = claims_obj.get("claims") if isinstance(claims_obj, dict) else None
    if not isinstance(claims, list):
        raise ValueError(f"{label}: claims must be a list")
    errors = census_brief.validate_claims(claims, rows)
    if errors:
        raise ValueError(f"{label}: citation boundary rejected: {errors[:3]}")
    return claims


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_artifacts(state: dict[str, Any]) -> dict[str, Any]:
    """Validate claims, render everything into a temp dir, rename atomically."""
    reduced = state["reduced"]
    rows = state["findings_input"]["rows"]
    findings = _validate_claims(state.get("findings_claims"), rows, "findings")
    onepager_claims = _validate_claims(state.get("onepager_claims"), rows, "onepager")
    out_dir = Path(state["out_dir"])
    if out_dir.exists():
        raise ValueError(f"out_dir exists: {out_dir}")
    run_id = str(uuid.uuid4())
    started = datetime.fromisoformat(
        state.get("run_started") or datetime.now(UTC).isoformat()
    )
    summaries_on = str(state.get("persons_llm", "")).lower() == "true"
    onepager = _onepager(state, reduced, onepager_claims, run_id)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".org-ai-dossier-", dir=out_dir.parent))
    try:
        docs = {
            "onepager.md": onepager,
            "dossier.md": _dossier(state, reduced, findings, summaries_on),
            "repos.md": _repos_md(state, reduced),
            "jira.md": _jira_md(state, reduced),
        }
        paths: dict[str, Path] = {}
        for name, text in docs.items():
            (tmp / name).write_text(text + "\n", encoding="utf-8")
            paths[name] = tmp / name
        paths.update(
            _write_ledgers(
                tmp,
                reduced,
                raw={
                    "repo_findings": list(state.get("repo_findings") or []),
                    "jira_findings": list(state.get("jira_findings") or []),
                    "person_summaries": list(state.get("person_summaries") or []),
                },
            )
        )
        record = RunRecord(
            run_id=run_id,
            started=started,
            finished=datetime.now(UTC),
            org=state["org"],
            window_days=int(state["window_days"]),
            visibility=[
                v.strip() for v in str(state["visibility"]).split(",") if v.strip()
            ],
            persons_llm=summaries_on,
            persons_llm_ack=(state.get("persons_llm_ack") or None)
            if summaries_on
            else None,
            head_sha=_head_sha(),
            graph_sha256=_sha256(GRAPH_PATH) if GRAPH_PATH.exists() else "0" * 64,
            deployment=os.environ.get("AZURE_MODEL", ""),
            prompt_versions=PROMPT_VERSIONS,
            api_calls_estimated=int(state.get("api_calls_estimated", 0)),
            api_calls_actual=int(state.get("api_calls_actual", 0)),
            llm_calls_estimated=int(state.get("llm_calls_estimated", 0)),
            llm_calls_actual=int(reduced.get("llm_calls_actual", 0))
            + len(state.get("person_summaries") or [])
            + 2,
            coverage=reduced["coverage"],
            artifact_sha256={k: _sha256(p) for k, p in paths.items()},
            canaries=reduced["canaries"],
        )
        (tmp / "run.json").write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )
        paths["run.json"] = tmp / "run.json"
        os.replace(tmp, out_dir)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return {"artifacts": {k: str(out_dir / k) for k in paths}}
