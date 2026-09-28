"""FR-1130 gh-issues census report: memo glue, refusing crosstab, verify.

The memo glue re-implements the person_profile_census pair/merge contract
for gh-issues bundles. `gh_issues_crosstab` refuses any unresolved, unknown,
duplicate, missing, off-taxonomy or canary-contradicting ledger row before it
writes a byte of output. `verify_citations` and `check_dispositions` back the
`python -m ... gh_issues_report verify <results-dir>` entry.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from yamlgraph.models.map_results import MapFailure

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
gia = importlib.import_module(
    "examples.demos.corpus_census.adapters.gh_issues_adapters"
)

TAXONOMY = [
    "spam-invalid",
    "docs",
    "maintenance-non-pain",
    "interrupt-resume-hitl",
    "subgraph-config-propagation",
    "checkpoint-persistence",
    "streaming",
    "state-schema-reducers",
    "control-flow-routing",
    "functional-api",
    "prebuilt-agents-tools",
    "model-provider-integration",
    "platform-server-cli-sdk",
    "observability-visualization",
    "error-handling-retry",
    "async-concurrency-performance",
    "typing-api-ergonomics",
]
SIGNATURE_FILES = [
    "examples/demos/langgraph_issues_census/graph.yaml",
    "examples/demos/corpus_census/prompts/judge_item.yaml",
    "examples/demos/corpus_census/tools.py",
    "examples/demos/corpus_census/adapters/gh_issues_adapters.py",
    "examples/demos/corpus_census/adapters/gh_issues_report.py",
]
MAX_CITATIONS = 5
TOP_LABELS = 5
SECTIONS = ("solves", "inherits", "untouched")


class CategoryCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: int
    issues_open: int
    issues_closed: int
    prs_open: int
    prs_closed: int


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str
    labels: list[str]


class CensusManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    repository: str
    source: str
    snapshot_retrieved_at: str
    snapshot_count: int
    snapshot_sha256: str
    provider: str
    model: str
    rows: int
    signature_sha256: dict[str, str | None]
    ledger_sha256: str
    crosstab_sha256: str
    categories: dict[str, CategoryCounts]
    citations: dict[str, list[Citation]]
    model_calls: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None


# Loaded by file path as a graph tool: resolve deferred annotations now.
for _model in (CategoryCounts, Citation, CensusManifest):
    _model.model_rebuild(_types_namespace=globals())


# --- memo glue --------------------------------------------------------------


def gh_issues_memo_prepare(state: dict[str, Any] | None = None, **_: Any) -> dict:
    """Require `memo_store`; build the memo signature inputs and version query."""
    state = state or {}
    store = state.get("memo_store")
    if not isinstance(store, str) or not store.strip():
        raise ValueError("memo_store required: path of the census memo SQLite file")
    return {
        "memo_inputs": {
            k: state.get(k) for k in ("rubric", "labels", "provider", "model")
        },
        "memo_query": {"source": state.get("source")},
        "executed_contents": [],
    }


def _cover(entries: list[tuple[Any, Any]], size: int, what: str) -> dict[int, Any]:
    covered: dict[int, Any] = {}
    for index, value in entries:
        if type(index) is not int or not 0 <= index < size:
            raise ValueError(f"{what} index {index!r} out of range 0..{size - 1}")
        if index in covered:
            raise ValueError(f"duplicate {what} for index {index}")
        covered[index] = value
    missing = sorted(set(range(size)) - set(covered))
    if missing:
        raise ValueError(f"{what} missing for indices: {missing}")
    return covered


def _index(entry: Any) -> Any:
    return entry.get("_map_index") if isinstance(entry, dict) else None


def gh_issues_pair(state: dict[str, Any] | None = None, **_: Any) -> dict:
    """Join executed bundles and judge outcomes by exact index covers."""
    state = state or {}
    size = len(state["memo"]["result"]["todo"])
    bundles = _cover(
        [(_index(e), e.get("value")) for e in state.get("executed_contents") or []],
        size,
        "bundle",
    )
    failures = [
        MapFailure.model_validate(raw)
        for raw in state.get("executed_findings_failures") or []
    ]
    outcomes = _cover(
        [
            *(
                (_index(f), ("finding", f))
                for f in state.get("executed_findings") or []
            ),
            *((f.index, ("error", f.message)) for f in failures),
        ],
        size,
        "outcome",
    )
    paired = []
    for index in range(size):
        kind, value = outcomes[index]
        if kind == "finding":
            value = {
                k: v
                for k, v in value.items()
                if k not in ("_map_index", "source_index")
            }
        paired.append({"_map_index": index, "bundle": bundles[index], kind: value})
    return {"paired": paired}


def gh_issues_findings(state: dict[str, Any] | None = None, **_: Any) -> dict:
    """Memo-merged records -> the items-aligned findings `reduce_ledger` reads."""
    state = state or {}
    records = state["merged"]["result"]["records"]
    by_index = _cover(
        [(_index(r), r) for r in records],
        len(state.get("items") or []),
        "merged record",
    )
    findings = []
    for index in sorted(by_index):
        record = by_index[index]
        if "error" in record:
            findings.append({"_map_index": index, "_error": record["error"]})
        else:
            findings.append({"_map_index": index, **record["finding"]})
    return {"findings": findings}


# --- crosstab -----------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _number(ref: str) -> int:
    return int(ref.rsplit("#", 1)[1])


def _labels(raw: Any) -> list[str]:
    labels = json.loads(raw) if isinstance(raw, str) else raw
    if labels != TAXONOMY:
        raise ValueError("labels must equal the frozen FR-1130 taxonomy, in order")
    return labels


def _checked_rows(state: dict[str, Any], by_ref: dict[str, Any]) -> dict[str, str]:
    """Return {ref: category} or raise on any unresolved or inconsistent row."""
    path = Path(state["ledger"]["jsonl_path"])
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    selected = [str(ref) for ref in state.get("items") or []]
    judged: dict[str, str] = {}
    for row in rows:
        ref = row["item_ref"]
        if ref not in by_ref or ref not in selected:
            raise ValueError(f"ledger ref {ref} is not a selected snapshot item")
        if ref in judged:
            raise ValueError(f"ledger ref {ref} appears twice")
        if row.get("abstained") or row.get("judgement") == "abstain":
            reason = row.get("abstain_reason") or "abstain"
            raise ValueError(f"ledger ref {ref} unresolved: {reason}")
        if row["judgement"] not in TAXONOMY:
            raise ValueError(
                f"ledger ref {ref} judged off-taxonomy {row['judgement']!r}"
            )
        judged[ref] = row["judgement"]
    missing = sorted(set(selected) - set(judged), key=_number)
    if missing:
        raise ValueError(f"ledger missing selected refs: {missing}")
    fixture = json.loads(Path(state["fixture_path"]).read_text(encoding="utf-8"))
    for ref, expected in fixture["expected"].items():
        is_canary = expected["role"] == "canary" and ref in judged
        if is_canary and judged[ref] != expected["category"]:
            raise ValueError(
                f"canary {ref} judged {judged[ref]!r}, expected {expected['category']!r}"
            )
    return judged


def _tally(judged: dict[str, str], by_ref: dict[str, Any]) -> dict[str, CategoryCounts]:
    counts = {c: Counter() for c in TAXONOMY}
    for ref, category in judged.items():
        record = by_ref[ref]
        counts[category]["items"] += 1
        kind = "issues" if record.kind == "issue" else "prs"
        counts[category][f"{kind}_{record.state}"] += 1
    return {
        c: CategoryCounts(
            items=n["items"],
            issues_open=n["issues_open"],
            issues_closed=n["issues_closed"],
            prs_open=n["prs_open"],
            prs_closed=n["prs_closed"],
        )
        for c, n in counts.items()
    }


def _markdown(repo: str, rows: int, cats: dict, cites: dict, top: dict) -> str:
    lines = [
        f"# LangGraph issues census — `{repo}`",
        "",
        f"All figures are item counts (issues and PRs counted separately); {rows} rows.",
        "",
        "| category | item count | issues open | issues closed | PRs open | PRs closed |",
        "|---|---|---|---|---|---|",
    ]
    for c, n in cats.items():
        lines.append(
            f"| {c} | {n.items} | {n.issues_open} | {n.issues_closed} | "
            f"{n.prs_open} | {n.prs_closed} |"
        )
    lines += ["", "## Citations and top upstream labels", ""]
    for c in TAXONOMY:
        refs = ", ".join(f"#{_number(x.ref)}" for x in cites[c]) or "—"
        labels = ", ".join(f"{name} ({k})" for name, k in top[c]) or "—"
        lines.append(f"- **{c}** — citations: {refs}; labels: {labels}")
    return "\n".join(lines) + "\n"


def gh_issues_crosstab(state: dict[str, Any] | None = None, **_: Any) -> dict:
    """Refuse unresolved ledgers; write crosstab.md and manifest.json."""
    state = state or {}
    repo, mode, _value = gia.parse_source(str(state.get("source") or ""))
    _labels(state.get("labels"))
    snapshot = gia.load_snapshot(repo)
    by_ref = {f"{repo}#{r.number}": r for r in snapshot.items}
    judged = _checked_rows(state, by_ref)
    if mode == "all" and len(judged) != snapshot.count:
        raise ValueError(f"{len(judged)} rows != snapshot count {snapshot.count}")
    cats = _tally(judged, by_ref)
    if sum(n.items for n in cats.values()) != len(judged):
        raise ValueError("category item counts do not sum to the row count")
    cites: dict[str, list[Citation]] = {}
    top: dict[str, list[tuple[str, int]]] = {}
    for c in TAXONOMY:
        refs = sorted((r for r, j in judged.items() if j == c), key=_number)
        cites[c] = [
            Citation(ref=r, labels=by_ref[r].labels) for r in refs[:MAX_CITATIONS]
        ]
        top[c] = Counter(lbl for r in refs for lbl in by_ref[r].labels).most_common(
            TOP_LABELS
        )
    results = Path(state["results_dir"])
    results.mkdir(parents=True, exist_ok=True)
    crosstab = results / "crosstab.md"
    crosstab.write_text(
        _markdown(repo, len(judged), cats, cites, top), encoding="utf-8"
    )
    manifest = CensusManifest(
        run_id=uuid.uuid4().hex,
        repository=repo,
        source=str(state["source"]),
        snapshot_retrieved_at=snapshot.retrieved_at,
        snapshot_count=snapshot.count,
        snapshot_sha256=snapshot.sha256,
        provider=str(state.get("provider") or ""),
        model=str(state.get("model") or ""),
        rows=len(judged),
        signature_sha256={
            f: (_sha256(Path(f)) if Path(f).is_file() else None)
            for f in SIGNATURE_FILES
        },
        ledger_sha256=_sha256(Path(state["ledger"]["jsonl_path"])),
        crosstab_sha256=_sha256(crosstab),
        categories=cats,
        citations=cites,
    )
    manifest_path = results / "manifest.json"
    manifest_path.write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    return {
        "crosstab": {
            "markdown_path": str(crosstab),
            "manifest_path": str(manifest_path),
        }
    }


# --- verify -------------------------------------------------------------------


def verify_citations(results_dir: str | Path) -> str:
    """Resolve every cited ref via `gh api`; each displayed label must be live."""
    manifest = json.loads((Path(results_dir) / "manifest.json").read_text("utf-8"))
    repo = manifest["repository"]
    lines = []
    total = sum(c["items"] for c in manifest["categories"].values())
    if total != manifest["rows"]:
        raise ValueError(f"category item counts {total} != rows {manifest['rows']}")
    lines.append(f"category item counts sum to {total} rows")
    checked = 0
    for category, cites in manifest["citations"].items():
        for cite in cites:
            number = _number(cite["ref"])
            argv = [
                "gh",
                "api",
                "--jq",
                ".labels[].name",
                f"repos/{repo}/issues/{number}",
            ]
            done = subprocess.run(
                argv, capture_output=True, text=True, timeout=60, check=False
            )
            if done.returncode != 0:
                raise ValueError(
                    f"{cite['ref']} does not resolve: {done.stderr.strip()}"
                )
            live = {line for line in done.stdout.splitlines() if line}
            absent = [lbl for lbl in cite["labels"] if lbl not in live]
            if absent:
                raise ValueError(f"{cite['ref']} ({category}) lacks labels {absent}")
            checked += 1
            lines.append(f"ok {cite['ref']} {category} labels={cite['labels']}")
    lines.append(f"all citations resolve: {checked} refs checked via gh api")
    return "\n".join(lines) + "\n"


_REC = re.compile(
    r"^(accept|out of scope|candidate FR: \S.* — \S.*|already covered by (FR-\d+))$"
)
_PATH = re.compile(r"`([^`\s]+)`")


def _disposition_rows(text: str) -> dict[str, tuple[str, list[str]]]:
    rows: dict[str, tuple[str, list[str]]] = {}
    section = None
    for line in text.splitlines():
        heading = re.match(r"^## (\w+)\s*$", line)
        if heading:
            section = heading[1]
            if section not in SECTIONS:
                raise ValueError(f"unknown dispositions section {section!r}")
            continue
        if not line.startswith("| ") or line.startswith(("| category", "|---")):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if section is None or len(cells) != 6:
            raise ValueError(f"malformed dispositions row: {line!r}")
        if cells[0] in rows:
            raise ValueError(f"category {cells[0]} has two disposition rows")
        rows[cells[0]] = (section, cells)
    return rows


def check_dispositions(text: str, manifest: dict, repo_root: str | Path) -> None:
    """Enforce one typed row per category and the §4 per-section rules."""
    root = Path(repo_root)
    rows = _disposition_rows(text)
    if set(rows) != set(manifest["categories"]):
        raise ValueError(
            f"dispositions rows {sorted(rows)} != categories {sorted(manifest['categories'])}"
        )
    for category, (section, cells) in rows.items():
        counts = manifest["categories"][category]
        cited = " ".join(
            f"#{_number(c['ref'])}" for c in manifest["citations"][category]
        )
        expected = [
            f"{counts['issues_open']}/{counts['issues_closed']}",
            f"{counts['prs_open']}/{counts['prs_closed']}",
            cited,
        ]
        if cells[1:4] != expected:
            raise ValueError(f"{category}: counts/citations {cells[1:4]} != {expected}")
        evidence, rec = cells[4], cells[5]
        match = _REC.match(rec)
        if match is None:
            raise ValueError(f"{category}: recommendation {rec!r} is not a frozen form")
        if match[2] and not list((root / "feature-requests").glob(f"{match[2]}-*.md")):
            raise ValueError(f"{category}: {match[2]} names no existing FR file")
        if section == "solves":
            paths = [p for p in _PATH.findall(evidence) if (root / p).exists()]
            if not paths or not (rec == "accept" or match[2]):
                raise ValueError(
                    f"{category}: solves needs a repo path and accept/covered"
                )
        elif section == "inherits" and not (
            rec == "accept" or rec.startswith("candidate")
        ):
            raise ValueError(f"{category}: inherits recommends candidate FR or accept")
        elif section == "untouched" and rec != "out of scope":
            raise ValueError(f"{category}: untouched recommends out of scope")


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "verify":
        print(
            "usage: python -m ...gh_issues_report verify <results-dir>", file=sys.stderr
        )
        return 2
    results = Path(argv[1])
    report = verify_citations(results)
    manifest = json.loads((results / "manifest.json").read_text("utf-8"))
    check_dispositions(
        (results / "dispositions.md").read_text("utf-8"), manifest, REPO_ROOT
    )
    report += "dispositions: one typed row per category; section rules hold\n"
    (results / "verify.txt").write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
