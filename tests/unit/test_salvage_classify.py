"""FR-868 salvage_classify graph — contract tests.

Deterministic surface only: schema, validators, and draft writer exposed
by the graph's nodes module. LLM classification is exercised by an
operator-run live pass over the real scripture-dev checkout, recorded in
the FR — never here (judgement R-4).
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO = REPO_ROOT / "examples" / "demos" / "salvage_classify"
GRAPH = DEMO / "graph.yaml"
NODES = DEMO / "nodes" / "salvage_tools.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "salvage" / "disposition-valid.json"


def load_module():
    spec = importlib.util.spec_from_file_location(NODES.stem, NODES)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture_data():
    return json.loads(FIXTURE.read_text())


# ── Shared runtime contract (REQ-YG-619) ───────────────────────────────


@pytest.mark.req("REQ-YG-619")
def test_graph_lints_clean():
    assert GRAPH.exists(), f"{GRAPH} missing"
    r = subprocess.run(
        [sys.executable, "-m", "yamlgraph.cli", "graph", "lint", str(GRAPH)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.req("REQ-YG-619")
def test_no_repo_mutation_tokens():
    sources = [GRAPH, NODES, *sorted(DEMO.glob("prompts/*.yaml"))]
    assert sources, "no sources found"
    for src in sources:
        text = src.read_text()
        for tok in ["git commit", "git push", "gh pr", "gh issue", "gh api"]:
            assert tok not in text, f"{tok!r} in {src}"


@pytest.mark.req("REQ-YG-619")
def test_write_drafts_confined_to_tmp_ramp(tmp_path, monkeypatch):
    mod = load_module()
    monkeypatch.chdir(tmp_path)
    result = mod.write_drafts(fixture_data())
    written = {Path(p) for p in result.values()}
    expected = {
        Path("tmp/ramp/salvage-disposition.md"),
        Path("tmp/ramp/salvage-disposition.json"),
    }
    assert {Path(*p.parts[-3:]) for p in written} == expected
    stray = [
        p for p in tmp_path.rglob("*") if p.is_file() and "tmp/ramp" not in p.as_posix()
    ]
    assert not stray, f"files written outside tmp/ramp: {stray}"


# ── Schema and validators (REQ-YG-618) ─────────────────────────────────


@pytest.mark.req("REQ-YG-618")
def test_fixture_validates_against_schema():
    mod = load_module()
    disp = mod.SalvageDisposition.model_validate(fixture_data())
    assert disp.manifest_count == len(disp.items)


@pytest.mark.req("REQ-YG-618")
def test_unknown_verdict_rejected():
    mod = load_module()
    data = fixture_data()
    data["items"][0]["verdict"] = "unknown"
    with pytest.raises(ValidationError):
        mod.SalvageDisposition.model_validate(data)


@pytest.mark.req("REQ-YG-618")
def test_count_mismatch_is_validation_error():
    mod = load_module()
    data = fixture_data()
    manifest = [i["path"] for i in data["items"]] + ["extra/file.txt"]
    errors = mod.validate_disposition(data, manifest, REPO_ROOT)
    assert any("count" in e.lower() or "extra/file.txt" in e for e in errors)


@pytest.mark.req("REQ-YG-618")
def test_duplicate_must_name_existing_equivalent():
    mod = load_module()
    data = fixture_data()
    manifest = [i["path"] for i in data["items"]]
    assert mod.validate_disposition(data, manifest, REPO_ROOT) == []
    data["items"][0]["yamlgraph_equivalent"] = "no/such/path.py"
    errors = mod.validate_disposition(data, manifest, REPO_ROOT)
    assert any("no/such/path.py" in e for e in errors)


@pytest.mark.req("REQ-YG-618")
def test_duplicate_without_equivalent_rejected():
    mod = load_module()
    data = fixture_data()
    data["items"][0]["yamlgraph_equivalent"] = None
    manifest = [i["path"] for i in data["items"]]
    errors = mod.validate_disposition(data, manifest, REPO_ROOT)
    assert errors, "duplicate with no equivalent must be a validation error"


@pytest.mark.req("REQ-YG-618")
def test_lift_destination_outside_namespace_rejected():
    mod = load_module()
    data = fixture_data()
    lift = next(i for i in data["items"] if i["verdict"] == "lift")
    lift["target_path"] = "yamlgraph/render.sh"
    manifest = [i["path"] for i in data["items"]]
    errors = mod.validate_disposition(data, manifest, REPO_ROOT)
    assert any("ramp/salvage" in e for e in errors)


@pytest.mark.req("REQ-YG-618")
def test_lift_requires_destination_and_rationale():
    mod = load_module()
    data = fixture_data()
    lift = next(i for i in data["items"] if i["verdict"] == "lift")
    lift["target_path"] = None
    manifest = [i["path"] for i in data["items"]]
    errors = mod.validate_disposition(data, manifest, REPO_ROOT)
    assert errors, "lift with no target_path must be a validation error"
    data2 = fixture_data()
    lift2 = next(i for i in data2["items"] if i["verdict"] == "lift")
    lift2["rationale"] = ""
    with pytest.raises(ValidationError):
        mod.SalvageDisposition.model_validate(data2)


@pytest.mark.req("REQ-YG-618")
def test_disposition_requires_source_sha():
    mod = load_module()
    data = fixture_data()
    data["source_sha"] = ""
    with pytest.raises(ValidationError):
        mod.SalvageDisposition.model_validate(data)
