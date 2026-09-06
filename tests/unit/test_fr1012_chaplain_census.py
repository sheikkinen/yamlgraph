"""FR-1012 Step 0 — Chaplain disposition census tooling witnesses (REQ-YG-666, CAP-264).

Deterministic, LLM-free. Covers: the frozen discovery rule, marker-AST fan-in
(never text regex), the payload contract, every preflight refusal happening
before any provider call, and every reconciler rejection the judgement lists
(illegal kind/verdict, abstained rows, unknown/duplicate/missing rows, invalid
evidence spans, unresolved manual review) plus the two cross-row rubric rules
code enforces (delete must not orphan a REQ; a mixed CAP is keep + manual).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ADAPTERS = REPO / "examples/demos/corpus_census/adapters"

# process: reads scripts/, examples/ and drives git in a fixture repo (FR-756)
pytestmark = [pytest.mark.req("REQ-YG-666"), pytest.mark.process]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ad():
    return _load("chaplain_adapters", ADAPTERS / "chaplain_adapters.py")


@pytest.fixture(scope="module")
def census():
    return _load("chaplain_census", REPO / "scripts/chaplain_census.py")


def _git(root: Path, *argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=root, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A tiny git checkout with two candidate tests, one outside witness, one runtime CAP, one mixed CAP."""
    root = tmp_path / "repo"
    (root / "tests/unit").mkdir(parents=True)
    (root / "capabilities").mkdir()
    (root / "scripts").mkdir()
    (root / ".chaplain/scripts").mkdir(parents=True)
    (root / ".chaplain/scripts/start-system.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (root / "scripts/live_thing.py").write_text("LIVE = 1\n", encoding="utf-8")
    (root / "tests/unit/test_watcher_fsm.py").write_text(
        'import pytest\n\n@pytest.mark.req("REQ-YG-900")\ndef test_fsm():\n    assert ".chaplain/config" \n', encoding="utf-8"
    )
    (root / "tests/unit/test_live_gate.py").write_text(
        'import pytest\n\n@pytest.mark.req("REQ-YG-901")\ndef test_triage_gate():\n    assert "triage" \n', encoding="utf-8"
    )
    (root / "tests/unit/test_core_outside.py").write_text(
        'import pytest\n\n@pytest.mark.req("REQ-YG-901")\ndef test_core():\n    assert 1\n', encoding="utf-8"
    )
    (root / "capabilities/CAP-900-watcher.yaml").write_text(
        "id: CAP-900\nname: Watcher\nstatus: active\nmodules:\n  - .chaplain/scripts/start-system.sh\nrequirements:\n  - id: REQ-YG-900\n    description: watcher fsm\n    modules:\n      - .chaplain/scripts/start-system.sh\nfr: FR-1\n",
        encoding="utf-8",
    )
    (root / "capabilities/CAP-901-mixed.yaml").write_text(
        "id: CAP-901\nname: Mixed chaplain and live\nmodules:\n  - .chaplain/watch.sh\n  - scripts/live_thing.py\nrequirements:\n  - id: REQ-YG-901\n    description: live gate\n    modules:\n      - scripts/live_thing.py\nfr: FR-2\n",
        encoding="utf-8",
    )
    _git(root, "init", "-q")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "fixture")
    return root


# --- discovery + facts ------------------------------------------------------------


def test_discovery_rule_is_sorted_unique_and_selects_by_needle(ad, repo):
    items = ad.discover_paths(repo)
    assert items == sorted(set(items))
    assert "tests/unit/test_watcher_fsm.py" in items
    assert "tests/unit/test_live_gate.py" in items  # mentions "triage" → candidate; semantics are the model's
    assert "tests/unit/test_core_outside.py" not in items
    assert "capabilities/CAP-900-watcher.yaml" in items and "capabilities/CAP-901-mixed.yaml" in items


def test_manifest_fan_in_counts_only_tests_outside_the_candidate_set(ad, repo):
    rows = {r["path"]: r for r in ad.build_manifest(repo, "deadbeef")}
    assert rows["tests/unit/test_watcher_fsm.py"]["fan_in_by_req"] == {"REQ-YG-900": 0}
    assert rows["tests/unit/test_live_gate.py"]["fan_in_by_req"] == {"REQ-YG-901": 1}
    cap = rows["capabilities/CAP-901-mixed.yaml"]
    assert cap["modules_present"] == {".chaplain/watch.sh": False, "scripts/live_thing.py": True}
    assert cap["surviving_witnesses_by_req"] == {"REQ-YG-901": ["tests/unit/test_core_outside.py"]}
    assert cap["current_status"] == "active" and rows["capabilities/CAP-900-watcher.yaml"]["cap_id"] == "CAP-900"
    assert all(len(r["sha256"]) == 64 and r["bytes"] > 0 for r in rows.values())


def test_reqs_come_from_marker_ast_not_text(ad, tmp_path):
    p = tmp_path / "test_x.py"
    p.write_text('"""mentions REQ-YG-999 in prose."""\nimport pytest\n\n@pytest.mark.req("REQ-YG-100")\ndef test_a():\n    pass\n', encoding="utf-8")
    assert ad.marker_reqs(tmp_path, ["test_x.py"]) == {"test_x.py": ["REQ-YG-100"]}


def test_extract_payload_is_facts_then_file_text(ad, repo, monkeypatch):
    rows = ad.build_manifest(repo, "deadbeef")
    manifest = repo / "docs/census/chaplain-disposition-input.jsonl"
    ad.write_manifest(rows, manifest)
    monkeypatch.setenv(ad.MANIFEST_ENV, str(manifest))
    payload = ad.chaplain_extract({"item": "tests/unit/test_watcher_fsm.py"})
    assert payload.startswith("Facts (computed by code")
    assert ad.PAYLOAD_SEPARATOR in payload and payload.rstrip().endswith('assert ".chaplain/config"')
    with pytest.raises(KeyError):
        ad.chaplain_extract({"item": "tests/unit/not_in_manifest.py"})


# --- reconciler -----------------------------------------------------------------


def _generic(ad, repo, verdicts: dict[str, str], **overrides):
    rows = {r["path"]: r for r in ad.build_manifest(repo, "deadbeef")}
    out = []
    for path, label in verdicts.items():
        span = "Facts (computed by code; treat as ground truth):"
        row = {"item_ref": path, "judgement": label, "confidence": 0.9, "evidence_span": span, "model": "m", "prompt_version": "judge_item.v1", "abstained": False, "abstain_reason": "", "disagreement": False, "raw_judgement": label, "repaired": False}
        row.update(overrides.get(path, {}))
        out.append(row)
    return out, rows


ALL = {
    "tests/unit/test_watcher_fsm.py": "delete",
    "tests/unit/test_live_gate.py": "keep",
    "capabilities/CAP-900-watcher.yaml": "retire",
    "capabilities/CAP-901-mixed.yaml": "retire",
}


def test_reconcile_applies_both_cross_row_rules(ad, repo):
    generic, manifest = _generic(ad, repo, ALL)
    rows = {r.path: r for r in ad.reconcile(generic, manifest, repo)}
    # watcher test: REQ-YG-900 fan-in 0 but CAP-900 retires it → delete stands
    assert rows["tests/unit/test_watcher_fsm.py"].verdict == "delete" and not rows["tests/unit/test_watcher_fsm.py"].manual_review
    assert rows["capabilities/CAP-900-watcher.yaml"].verdict == "retire"
    # mixed CAP: live REQ witnessed outside + present non-runtime module → keep + manual
    mixed = rows["capabilities/CAP-901-mixed.yaml"]
    assert mixed.verdict == "keep" and mixed.manual_review and "mixed CAP" in mixed.reason
    assert ad.unresolved(rows.values()) == ["capabilities/CAP-901-mixed.yaml"]


def test_delete_that_would_orphan_a_req_becomes_manual(ad, repo):
    verdicts = dict(ALL, **{"capabilities/CAP-900-watcher.yaml": "keep"})
    generic, manifest = _generic(ad, repo, verdicts)
    rows = {r.path: r for r in ad.reconcile(generic, manifest, repo)}
    t = rows["tests/unit/test_watcher_fsm.py"]
    assert t.verdict == "keep" and t.manual_review and "orphan" in t.reason


@pytest.mark.parametrize(
    ("path", "label"),
    [("tests/unit/test_watcher_fsm.py", "retire"), ("capabilities/CAP-900-watcher.yaml", "delete"), ("tests/unit/test_live_gate.py", "maybe")],
)
def test_illegal_kind_verdict_pairs_are_rejected(ad, repo, path, label):
    generic, manifest = _generic(ad, repo, dict(ALL, **{path: label}))
    with pytest.raises(ad.ReconcileError, match="illegal verdict"):
        ad.reconcile(generic, manifest, repo)


def test_abstained_row_is_rejected_unless_resolved(ad, repo):
    over = {"tests/unit/test_live_gate.py": {"judgement": "abstain", "abstained": True, "abstain_reason": "unclear", "evidence_span": ""}}
    generic, manifest = _generic(ad, repo, ALL, **over)
    with pytest.raises(ad.ReconcileError, match="abstained"):
        ad.reconcile(generic, manifest, repo)
    res = {"tests/unit/test_live_gate.py": {"verdict": "keep", "reason": "live gate", "resolved_by": "operator", "date": "2026-09-06"}}
    rows = {r.path: r for r in ad.reconcile(generic, manifest, repo, res)}
    assert rows["tests/unit/test_live_gate.py"].verdict == "keep" and "human resolution" in rows["tests/unit/test_live_gate.py"].reason


def test_unknown_duplicate_and_missing_rows_are_rejected(ad, repo):
    generic, manifest = _generic(ad, repo, ALL)
    with pytest.raises(ad.ReconcileError, match="unknown item_ref"):
        ad.reconcile(generic + [dict(generic[0], item_ref="tests/unit/ghost.py")], manifest, repo)
    with pytest.raises(ad.ReconcileError, match="duplicate"):
        ad.reconcile(generic + [generic[0]], manifest, repo)
    with pytest.raises(ad.ReconcileError, match="without a generic row"):
        ad.reconcile(generic[1:], manifest, repo)


def test_invalid_evidence_span_is_rejected(ad, repo):
    generic, manifest = _generic(ad, repo, ALL, **{"tests/unit/test_watcher_fsm.py": {"evidence_span": "this text is nowhere in the payload"}})
    with pytest.raises(ad.ReconcileError, match="evidence_span"):
        ad.reconcile(generic, manifest, repo)


def test_manual_review_label_maps_to_keep_plus_flag(ad, repo):
    generic, manifest = _generic(ad, repo, dict(ALL, **{"tests/unit/test_live_gate.py": "manual_review"}))
    rows = {r.path: r for r in ad.reconcile(generic, manifest, repo)}
    assert rows["tests/unit/test_live_gate.py"].verdict == "keep" and rows["tests/unit/test_live_gate.py"].manual_review


# --- wrapper preflight refusals (before any provider call) ------------------------------


def test_ceilings_and_canaries_are_the_frozen_values(census):
    assert (census.MAX_ITEMS, census.MAX_TOTAL_BYTES, census.MAX_ITEM_BYTES, census.MAX_CALLS, census.TIMEOUT_S) == (120, 1_500_000, 48 * 1024, 130, 1200)
    assert census.CANARIES == {"tests/unit/test_fr305_watcher_pipeline_v2.py": "delete", "tests/unit/test_fr_triage.py": "keep"}
    rubric = (ADAPTERS / "chaplain_rubric.md").read_text(encoding="utf-8")
    assert not any(Path(p).name in rubric for p in census.CANARIES), "canaries must be withheld from the rubric"


def test_preflight_refuses_before_any_graph_call(census, ad, repo, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(census, "REPO_ROOT", repo)
    monkeypatch.setattr(census, "run_graph", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(census, "PREREQUISITES", {})
    # 1) oversize item
    monkeypatch.setattr(census, "MAX_ITEM_BYTES", 10)
    rc = census.main(["--out-dir", str(tmp_path / "o1")])
    assert rc == census.EX_CONTRACT and calls == []
    record = json.loads((tmp_path / "o1/chaplain-test-disposition.run.json").read_text(encoding="utf-8"))
    assert any("over 48 KB" in p for p in record["preflight_problems"])
    monkeypatch.setattr(census, "MAX_ITEM_BYTES", 48 * 1024)
    # 2) too many items
    monkeypatch.setattr(census, "MAX_ITEMS", 1)
    assert census.main(["--out-dir", str(tmp_path / "o2")]) == census.EX_CONTRACT and calls == []
    monkeypatch.setattr(census, "MAX_ITEMS", 120)
    # 3) call ceiling
    monkeypatch.setattr(census, "MAX_CALLS", 2)
    assert census.main(["--out-dir", str(tmp_path / "o3")]) == census.EX_CONTRACT and calls == []
    monkeypatch.setattr(census, "MAX_CALLS", 130)
    # 4) ancestry
    monkeypatch.setattr(census, "PREREQUISITES", {"FR-X": "0000000000000000000000000000000000000000"})
    assert census.main(["--out-dir", str(tmp_path / "o4")]) == census.EX_CONTRACT and calls == []
    monkeypatch.setattr(census, "PREREQUISITES", {})
    # 5) credential-shaped content
    # keep the needle ("triage") so the file stays a census candidate and is scanned
    (repo / "tests/unit/test_live_gate.py").write_text('TOKEN = "ghp_' + "A" * 36 + '"  # triage\n', encoding="utf-8")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "leak")
    assert census.main(["--out-dir", str(tmp_path / "o5")]) == census.EX_CONTRACT and calls == []
    # 6) dirty tree
    (repo / "tests/unit/test_live_gate.py").write_text("changed\n", encoding="utf-8")
    assert census.main(["--out-dir", str(tmp_path / "o6")]) == census.EX_CONTRACT and calls == []


def test_preflight_only_writes_manifest_and_record_without_running_graph(census, repo, monkeypatch, tmp_path):
    monkeypatch.setattr(census, "REPO_ROOT", repo)
    monkeypatch.setattr(census, "PREREQUISITES", {})
    monkeypatch.setattr(census, "run_graph", lambda *a, **k: pytest.fail("graph must not run in --preflight"))
    assert census.main(["--preflight", "--out-dir", str(tmp_path / "o")]) == 0
    manifest = (tmp_path / "o/chaplain-disposition-input.jsonl").read_text(encoding="utf-8").splitlines()
    record = json.loads((tmp_path / "o/chaplain-test-disposition.run.json").read_text(encoding="utf-8"))
    assert len(manifest) == record["counts"]["items"] == 4 and record["preflight_problems"] == []
    assert record["provider"] == "anthropic" and record["model"] == "claude-haiku-4-5" and record["visibility_data_classification"]
