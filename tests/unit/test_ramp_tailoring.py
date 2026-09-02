"""FR-866 ramp tailoring graphs — contract tests.

Deterministic surface only: collection, schemas, validators, and draft
writers exposed by each graph's nodes module. LLM behavior is exercised
by operator-run smokes recorded in the FR, never here.
"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMOS = REPO_ROOT / "examples" / "demos"
FIXTURE_TARGET = REPO_ROOT / "tests" / "fixtures" / "ramp_target"

GRAPHS = {
    "ramp_doctrine": DEMOS / "ramp_doctrine" / "graph.yaml",
    "ramp_rtm": DEMOS / "ramp_rtm" / "graph.yaml",
    "ramp_incidents": DEMOS / "ramp_incidents" / "graph.yaml",
}
NODES = {
    "ramp_doctrine": DEMOS / "ramp_doctrine" / "nodes" / "doctrine_tools.py",
    "ramp_rtm": DEMOS / "ramp_rtm" / "nodes" / "rtm_tools.py",
    "ramp_incidents": DEMOS / "ramp_incidents" / "nodes" / "incident_tools.py",
}


def load_module(name: str):
    path = NODES[name]
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Shared contract (REQ-YG-617) ────────────────────────────────────────


@pytest.mark.req("REQ-YG-617")
@pytest.mark.parametrize("name", sorted(GRAPHS))
def test_graph_lints_clean(name):
    graph = GRAPHS[name]
    assert graph.exists(), f"{graph} missing"
    r = subprocess.run(
        [sys.executable, "-m", "yamlgraph.cli", "graph", "lint", str(graph)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.req("REQ-YG-617")
@pytest.mark.parametrize("name", sorted(GRAPHS))
def test_no_repo_mutation_tokens(name):
    sources = [GRAPHS[name], NODES[name]]
    sources += sorted(GRAPHS[name].parent.glob("prompts/*.yaml"))
    for src in sources:
        text = src.read_text(encoding="utf-8")
        for tok in ["git commit", "git push", "gh pr", "gh issue", "gh api"]:
            assert tok not in text, f"{tok!r} in {src}"


@pytest.mark.req("REQ-YG-617")
@pytest.mark.parametrize(
    ("name", "stem"),
    [
        ("ramp_doctrine", "doctrine-draft"),
        ("ramp_rtm", "rtm-draft"),
        ("ramp_incidents", "incidents-draft"),
    ],
)
def test_write_drafts_only_under_tmp_ramp(tmp_path, name, stem):
    mod = load_module(name)
    md, js = mod.write_drafts(mod.EXAMPLE_DRAFT, base_dir=tmp_path)
    assert Path(md) == tmp_path / "tmp" / "ramp" / f"{stem}.md"
    assert Path(js) == tmp_path / "tmp" / "ramp" / f"{stem}.json"
    written = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert sorted(str(p) for p in written) == sorted([md, js])
    json.loads(Path(js).read_text(encoding="utf-8"))


# ── ramp_doctrine (REQ-YG-614) ──────────────────────────────────────────


@pytest.mark.req("REQ-YG-614")
def test_collect_doctrine_families_and_ids():
    mod = load_module("ramp_doctrine")
    items = mod.collect_doctrine(str(REPO_ROOT))
    families = {i["family"] for i in items}
    assert families == {"trap", "cure", "question"}
    ids = {i["id"] for i in items}
    assert "continuation_bias" in ids
    assert "read_raw_output_first" in ids
    assert all(i["text"] for i in items)


@pytest.mark.req("REQ-YG-614")
def test_collect_inventory_fixture_target():
    mod = load_module("ramp_doctrine")
    inv = mod.collect_inventory(str(FIXTURE_TARGET))
    assert any("publish.yml" in w for w in inv["workflow_triggers"])
    assert any("api.py" in s for s in inv["effect_sites"])
    assert inv["gates"] == []


@pytest.mark.req("REQ-YG-614")
def test_doctrine_verdict_schema():
    mod = load_module("ramp_doctrine")
    v = mod.DoctrineVerdict(
        family="trap",
        id="continuation_bias",
        verdict="applies",
        reason="publisher generates text unattended",
        target_evidence="src/publisher/api.py posts unreviewed output",
    )
    assert v.verdict == "applies"
    with pytest.raises(ValidationError):
        mod.DoctrineVerdict(
            family="saga", id="x", verdict="applies", reason="", target_evidence=""
        )


@pytest.mark.req("REQ-YG-614")
def test_validate_doctrine_rejects_invented_id():
    mod = load_module("ramp_doctrine")
    source = [{"family": "trap", "id": "continuation_bias", "text": "..."}]
    good = [
        {
            "family": "trap",
            "id": "continuation_bias",
            "verdict": "applies",
            "reason": "r",
            "target_evidence": "src/publisher/api.py",
        }
    ]
    invented = [
        {
            "family": "trap",
            "id": "totally_new_trap",
            "verdict": "applies",
            "reason": "r",
            "target_evidence": "e",
        }
    ]
    assert mod.validate_draft(good, source) == []
    errors = mod.validate_draft(invented, source)
    assert errors and "totally_new_trap" in " ".join(errors)


@pytest.mark.req("REQ-YG-614")
def test_write_drafts_scrubs_source_citations(tmp_path):
    mod = load_module("ramp_doctrine")
    draft = {
        "target": "/x",
        "inventory": {},
        "items": [
            {
                "family": "trap",
                "id": "composition_bug",
                "text": "trace the chain (ninchat_voice: FR-371 replay, NC-141 loop)",
                "verdict": "applies",
                "reason": "seen in FR-465 arc",
                "target_evidence": "src/publisher/api.py",
            }
        ],
        "all_dispositions": [
            {
                "family": "cure",
                "id": "callsite_fix",
                "verdict": "not",
                "reason": "generic; see FR-372 for the source arc",
                "target_evidence": "",
            }
        ],
    }
    md, js = mod.write_drafts(draft, base_dir=tmp_path)
    for path in (md, js):
        text = Path(path).read_text(encoding="utf-8")
        assert not re.search(r"\b(?:FR|NC)-\d+\b", text), path


@pytest.mark.req("REQ-YG-614")
def test_validate_doctrine_requires_evidence_and_reason():
    mod = load_module("ramp_doctrine")
    source = [{"family": "cure", "id": "callsite_fix", "text": "..."}]
    no_evidence = [
        {
            "family": "cure",
            "id": "callsite_fix",
            "verdict": "applies",
            "reason": "r",
            "target_evidence": "",
        }
    ]
    no_reason = [
        {
            "family": "cure",
            "id": "callsite_fix",
            "verdict": "not",
            "reason": "",
            "target_evidence": "",
        }
    ]
    assert mod.validate_draft(no_evidence, source)
    assert mod.validate_draft(no_reason, source)


# ── ramp_rtm (REQ-YG-615) ───────────────────────────────────────────────


@pytest.mark.req("REQ-YG-615")
def test_collect_tests_fixture_inventory():
    mod = load_module("ramp_rtm")
    inv = mod.collect_tests(str(FIXTURE_TARGET))
    files = {i["path"] for i in inv}
    assert any(p.endswith("tests/test_api.py") for p in files)
    names = {n for i in inv for n in i["tests"]}
    assert "test_title_cap_enforced" in names
    assert "test_edge_clamped_to_max" in names
    assert len(names) == 5


@pytest.mark.req("REQ-YG-615")
def test_rtm_entry_schema_forces_proposed():
    mod = load_module("ramp_rtm")
    e = mod.RtmEntry(
        req_id="REQ-FT-001",
        statement="Titles longer than the gallery cap are rejected.",
        witness_tests=["test_title_cap_enforced"],
        confidence=0.9,
        status="proposed",
    )
    assert e.status == "proposed"
    with pytest.raises(ValidationError):
        mod.RtmEntry(
            req_id="REQ-FT-002",
            statement="s",
            witness_tests=["t"],
            confidence=0.5,
            status="accepted",
        )


@pytest.mark.req("REQ-YG-615")
def test_validate_rtm_rejects_unknown_witness():
    mod = load_module("ramp_rtm")
    inv = mod.collect_tests(str(FIXTURE_TARGET))
    good = [
        {
            "req_id": "REQ-FT-001",
            "statement": "s",
            "witness_tests": ["test_title_cap_enforced"],
            "confidence": 0.9,
            "status": "proposed",
        }
    ]
    bad = [
        {
            "req_id": "REQ-FT-002",
            "statement": "s",
            "witness_tests": ["test_does_not_exist"],
            "confidence": 0.9,
            "status": "proposed",
        }
    ]
    assert mod.validate_rtm(good, inv) == []
    errors = mod.validate_rtm(bad, inv)
    assert errors and "test_does_not_exist" in " ".join(errors)


@pytest.mark.req("REQ-YG-615")
def test_rtm_gap_list_reports_unwitnessed_tests():
    mod = load_module("ramp_rtm")
    inv = mod.collect_tests(str(FIXTURE_TARGET))
    entries = [
        {
            "req_id": "REQ-FT-001",
            "statement": "s",
            "witness_tests": ["test_title_cap_enforced"],
            "confidence": 0.9,
            "status": "proposed",
        }
    ]
    gaps = mod.gap_tests(entries, inv)
    assert "test_edge_clamped_to_max" in gaps
    assert "test_title_cap_enforced" not in gaps
    assert len(gaps) == 4


# ── ramp_incidents (REQ-YG-616) ─────────────────────────────────────────


@pytest.mark.req("REQ-YG-616")
def test_collect_corpus_mentions_only():
    mod = load_module("ramp_incidents")
    corpus = mod.collect_corpus(str(REPO_ROOT), "deviant-daily")
    assert corpus, "corpus empty — FR-863 mentions deviant-daily"
    assert any("FR-863" in p for p in corpus)
    for p in corpus:
        assert "deviant-daily" in Path(REPO_ROOT, p).read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-616")
def test_incident_classification_schema():
    mod = load_module("ramp_incidents")
    inc = mod.IncidentClassification(
        verdict="incident",
        date="2026-08-23",
        defect="vision payload exceeded provider ceiling",
        root_cause="unclamped image edge",
        cure="MAX_EDGE clamp at boundary",
        witness="test_edge_clamped_to_max",
        source_ref="feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md",
    )
    assert inc.verdict == "incident"
    non = mod.IncidentClassification(verdict="not_an_incident")
    assert non.verdict == "not_an_incident"
    with pytest.raises(ValidationError):
        mod.IncidentClassification(verdict="incident", date="2026-08-23")


@pytest.mark.req("REQ-YG-616")
def test_validate_disposition_count_reconciliation():
    mod = load_module("ramp_incidents")
    corpus = ["docs/diary/a.md", "docs/diary/b.md"]
    complete = [
        {"path": "docs/diary/a.md", "verdict": "not_an_incident"},
        {
            "path": "docs/diary/b.md",
            "verdict": "incident",
            "date": "2026-08-23",
            "defect": "d",
            "root_cause": "r",
            "cure": "c",
            "witness": "w",
            "source_ref": "README.md",
        },
    ]
    dropped = complete[:1]
    assert mod.validate_disposition(complete, corpus, source_repo=str(REPO_ROOT)) == []
    errors = mod.validate_disposition(dropped, corpus, source_repo=str(REPO_ROOT))
    assert errors and "b.md" in " ".join(errors)


@pytest.mark.req("REQ-YG-616")
def test_validate_disposition_requires_resolvable_source_ref():
    mod = load_module("ramp_incidents")
    corpus = ["docs/diary/a.md"]
    bad_ref = [
        {
            "path": "docs/diary/a.md",
            "verdict": "incident",
            "date": "2026-08-23",
            "defect": "d",
            "root_cause": "r",
            "cure": "c",
            "witness": "w",
            "source_ref": "docs/diary/nonexistent-file.md",
        }
    ]
    errors = mod.validate_disposition(bad_ref, corpus, source_repo=str(REPO_ROOT))
    assert errors and "nonexistent-file.md" in " ".join(errors)
