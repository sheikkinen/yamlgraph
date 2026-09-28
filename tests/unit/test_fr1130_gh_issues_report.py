"""FR-1130 AC-09..AC-13: memo glue, crosstab refusals, citations, dispositions."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from examples.demos.corpus_census.adapters import gh_issues_adapters as gia
from examples.demos.corpus_census.adapters import gh_issues_report as gir

pytestmark = pytest.mark.process

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "fr1130" / "raw_read.json"
DATA = json.loads(FIXTURE.read_text(encoding="utf-8"))
RECORDS = DATA["records"]
EXPECTED = DATA["expected"]
REPO = "langchain-ai/langgraph"
REFS = [f"{REPO}#{n}" for n in sorted(r["number"] for r in RECORDS)]
LABELS = gir.TAXONOMY


@pytest.fixture
def workdir(tmp_path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    stdout = "".join(json.dumps(r) + "\n" for r in RECORDS)
    done = subprocess.CompletedProcess([], 0, stdout, "")
    with patch.object(gia.subprocess, "run", lambda argv, **kw: done):
        gia.gh_issues_discover({"source": REPO})
    return tmp_path


def _row(ref: str, judgement: str, abstained: bool = False) -> dict:
    return {
        "item_ref": ref,
        "judgement": "abstain" if abstained else judgement,
        "confidence": 0.0 if abstained else 0.9,
        "evidence_span": "" if abstained else "x",
        "model": "m",
        "prompt_version": "judge_item.v1",
        "abstained": abstained,
        "abstain_reason": "row_failed: boom" if abstained else "",
        "disagreement": False,
        "raw_judgement": "",
        "repaired": False,
    }


def _state(workdir: Path, rows: list[dict], **overrides) -> dict:
    ledger = workdir / "ledger.jsonl"
    ledger.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    state = {
        "source": REPO,
        "items": list(REFS),
        "labels": json.dumps(LABELS),
        "provider": "azure",
        "model": "m",
        "fixture_path": str(FIXTURE),
        "results_dir": str(workdir / "results"),
        "ledger": {"jsonl_path": str(ledger)},
    }
    state.update(overrides)
    return state


def _truth_rows() -> list[dict]:
    return [_row(ref, EXPECTED[ref]["category"]) for ref in REFS]


# --- memo glue ------------------------------------------------------------


@pytest.mark.req("REQ-YG-717")
def test_memo_prepare_requires_store_and_carries_signature_inputs():
    with pytest.raises(ValueError, match="memo_store"):
        gir.gh_issues_memo_prepare({"source": REPO})
    out = gir.gh_issues_memo_prepare(
        {
            "memo_store": "s.db",
            "source": REPO,
            "rubric": "r",
            "labels": "[]",
            "provider": "azure",
            "model": "m",
        }
    )
    assert out["memo_inputs"] == {
        "rubric": "r",
        "labels": "[]",
        "provider": "azure",
        "model": "m",
    }
    assert out["memo_query"] == {"source": REPO}


@pytest.mark.req("REQ-YG-717")
def test_pair_then_findings_keeps_failures_as_row_failed():
    state = {
        "items": REFS[:3],
        "memo": {"result": {"todo": REFS[1:3]}},
        "executed_contents": [
            {"_map_index": 1, "value": "b1"},
            {"_map_index": 0, "value": "b0"},
        ],
        "executed_findings": [
            {"_map_index": 0, "source_index": 0, "judgement": "docs"},
        ],
        "executed_findings_failures": [
            {
                "map": "judge_items",
                "dispatch": "d",
                "index": 1,
                "error_type": "X",
                "message": "boom",
                "node": "judge_items",
                "tolerated": True,
            },
        ],
    }
    paired = gir.gh_issues_pair(state)["paired"]
    assert paired == [
        {"_map_index": 0, "bundle": "b0", "finding": {"judgement": "docs"}},
        {"_map_index": 1, "bundle": "b1", "error": "boom"},
    ]
    merged = {
        "result": {
            "records": [
                {"_map_index": 2, "bundle": "b1", "error": "boom"},
                {
                    "_map_index": 0,
                    "bundle": "z",
                    "finding": {"judgement": "spam-invalid"},
                },
                {"_map_index": 1, "bundle": "b0", "finding": {"judgement": "docs"}},
            ]
        }
    }
    findings = gir.gh_issues_findings({"items": REFS[:3], "merged": merged})["findings"]
    assert findings == [
        {"_map_index": 0, "judgement": "spam-invalid"},
        {"_map_index": 1, "judgement": "docs"},
        {"_map_index": 2, "_error": "boom"},
    ]


@pytest.mark.req("REQ-YG-717")
def test_findings_refuse_missing_or_duplicate_records():
    merged = {
        "result": {
            "records": [
                {"_map_index": 0, "bundle": "a", "finding": {"judgement": "docs"}}
            ]
        }
    }
    with pytest.raises(ValueError, match="missing"):
        gir.gh_issues_findings({"items": REFS[:2], "merged": merged})


# --- crosstab: AC-09 refusals ---------------------------------------------


@pytest.mark.req("REQ-YG-717")
def test_crosstab_writes_item_counts_and_manifest(workdir):
    out = gir.gh_issues_crosstab(_state(workdir, _truth_rows()))["crosstab"]
    text = Path(out["markdown_path"]).read_text(encoding="utf-8")
    assert "item count" in text.lower()
    assert "unique" not in text.lower()
    manifest = json.loads(Path(out["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["repository"] == REPO
    assert manifest["snapshot_count"] == len(RECORDS)
    assert manifest["rows"] == len(REFS)
    assert sum(c["items"] for c in manifest["categories"].values()) == len(REFS)
    assert list(manifest["categories"]) == LABELS
    assert manifest["categories"]["docs"]["items"] == 3
    assert manifest["model_calls"] is None


@pytest.mark.req("REQ-YG-717")
@pytest.mark.parametrize(
    "mutate",
    [
        "abstained",
        "unknown-ref",
        "duplicate-ref",
        "missing-ref",
        "canary-wrong",
        "off-taxonomy",
    ],
)
def test_crosstab_refuses(workdir, mutate):
    rows = _truth_rows()
    if mutate == "abstained":
        rows[0] = _row(rows[0]["item_ref"], "", abstained=True)
    elif mutate == "unknown-ref":
        rows[0]["item_ref"] = f"{REPO}#6100"
    elif mutate == "duplicate-ref":
        rows[1]["item_ref"] = rows[0]["item_ref"]
    elif mutate == "missing-ref":
        rows.pop()
    elif mutate == "canary-wrong":
        canary = next(r for r in rows if EXPECTED[r["item_ref"]]["role"] == "canary")
        canary["judgement"] = "docs"
    elif mutate == "off-taxonomy":
        rows[0]["judgement"] = "other"
    state = _state(workdir, rows)
    with pytest.raises(ValueError):
        gir.gh_issues_crosstab(state)
    assert not (workdir / "results" / "crosstab.md").exists()


# --- AC-10 citations --------------------------------------------------------


@pytest.mark.req("REQ-YG-717")
def test_citations_are_lowest_numbers_min3_max5(workdir):
    rows = [_row(ref, "docs") for ref in REFS]
    canary = next(r for r in rows if EXPECTED[r["item_ref"]]["role"] == "canary")
    canary["judgement"] = "spam-invalid"
    out = gir.gh_issues_crosstab(_state(workdir, rows))["crosstab"]
    manifest = json.loads(Path(out["manifest_path"]).read_text(encoding="utf-8"))
    docs = [c["ref"] for c in manifest["citations"]["docs"]]
    assert docs == [r for r in REFS if r != canary["item_ref"]][:5]
    assert [c["ref"] for c in manifest["citations"]["spam-invalid"]] == [
        canary["item_ref"]
    ]
    assert manifest["citations"]["streaming"] == []
    by_ref = {f"{REPO}#{r['number']}": r["labels"] for r in RECORDS}
    for cites in manifest["citations"].values():
        for cite in cites:
            assert cite["labels"] == by_ref[cite["ref"]]


@pytest.mark.req("REQ-YG-717")
def test_verify_checks_every_citation_against_github(workdir):
    out = gir.gh_issues_crosstab(_state(workdir, _truth_rows()))["crosstab"]
    results = Path(out["manifest_path"]).parent
    live = {r["number"]: r for r in RECORDS}
    calls: list[list[str]] = []

    def fake(argv, **kwargs):
        calls.append(list(argv))
        number = int(argv[-1].rsplit("/", 1)[1])
        labels = "\n".join(live[number]["labels"])
        return subprocess.CompletedProcess(argv, 0, labels + "\n", "")

    with patch.object(gir.subprocess, "run", fake):
        report = gir.verify_citations(results)
    cited = sum(
        len(v)
        for v in json.loads((results / "manifest.json").read_text())[
            "citations"
        ].values()
    )
    assert len(calls) == cited
    assert "all citations resolve" in report

    def lying(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, "\n", "")

    with patch.object(gir.subprocess, "run", lying), pytest.raises(ValueError):
        gir.verify_citations(results)


# --- AC-12 dispositions -----------------------------------------------------


def _dispositions(manifest: dict, override: dict | None = None) -> str:
    sections = {"solves": [], "inherits": [], "untouched": []}
    for category, counts in manifest["categories"].items():
        cites = " ".join(
            f"#{c['ref'].split('#')[1]}" for c in manifest["citations"][category]
        )
        section, evidence, rec = "untouched", "outside surface", "out of scope"
        if category == "docs":
            section, evidence, rec = "solves", "`reference/graph-yaml.md`", "accept"
        if category == "interrupt-resume-hitl":
            section, evidence, rec = (
                "inherits",
                "passes through",
                "candidate FR: X — do Y.",
            )
        if override and category in override:
            section, evidence, rec = override[category]
        sections[section].append(
            f"| {category} | {counts['issues_open']}/{counts['issues_closed']} | "
            f"{counts['prs_open']}/{counts['prs_closed']} | {cites} | {evidence} | {rec} |"
        )
    parts = ["# Dispositions", ""]
    for name, rows in sections.items():
        parts += [
            f"## {name}",
            "",
            "| category | issues open/closed | PRs open/closed | citations | YAMLGraph evidence | recommendation |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
        ]
    return "\n".join(parts)


@pytest.mark.req("REQ-YG-717")
def test_disposition_rules(workdir):
    out = gir.gh_issues_crosstab(_state(workdir, _truth_rows()))["crosstab"]
    manifest = json.loads(Path(out["manifest_path"]).read_text(encoding="utf-8"))
    repo_root = Path(__file__).resolve().parents[2]
    gir.check_dispositions(_dispositions(manifest), manifest, repo_root)
    bad = [
        {"docs": ("solves", "no path here", "accept")},
        {"docs": ("inherits", "x", "out of scope")},
        {"streaming": ("untouched", "x", "accept")},
        {
            "streaming": (
                "solves",
                "`reference/graph-yaml.md`",
                "already covered by FR-99999",
            )
        },
        {"streaming": ("inherits", "x", "maybe later")},
    ]
    for override in bad:
        with pytest.raises(ValueError):
            gir.check_dispositions(
                _dispositions(manifest, override), manifest, repo_root
            )
    missing_row = "\n".join(
        line
        for line in _dispositions(manifest).splitlines()
        if not line.startswith("| streaming ")
    )
    with pytest.raises(ValueError):
        gir.check_dispositions(missing_row, manifest, repo_root)
