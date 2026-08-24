"""Tests for FR-877: curation-state marker and staleness advisory.

All tests use temporary memory roots (judgement C-4).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "memory-curation"
ADVISORY = EXAMPLE / "advisory.py"
HOOK = REPO_ROOT / ".github" / "hooks" / "scripts" / "memory-advisory.sh"


def run_tool(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )


@pytest.fixture()
def memory_root(tmp_path: Path) -> Path:
    root = tmp_path / "memories"
    (root / "repo").mkdir(parents=True)
    (root / "repo" / "keepme.md").write_text("# Durable\nstill true\n")
    (root / "repo" / "stale.md").write_text("# Pin\nfoo v0.1.7\n")
    return root


def curate(memory_root: Path, out_dir: Path, verdicts: dict) -> None:
    """Full collect/reconcile/sign/apply cycle on a temp root."""
    import hashlib

    run_tool(
        EXAMPLE / "nodes" / "collect.py",
        "--memory-root",
        str(memory_root),
        "--out-dir",
        str(out_dir),
    )
    manifest = json.loads((out_dir / "manifest.json").read_text())
    rows = []
    for key in manifest["notes"]:
        row = {
            "path": key,
            "verdict": "keep",
            "audience": "machine_local",
            "rationale": "durable",
            "redacted_draft": None,
            "staleness": "fresh",
            "staleness_evidence": None,
        }
        row.update(verdicts.get(key, {}))
        rows.append(row)
    raw = out_dir / "raw.json"
    raw.write_text(json.dumps(rows))
    run_tool(
        EXAMPLE / "nodes" / "reconcile.py",
        "--manifest",
        str(out_dir / "manifest.json"),
        "--dispositions",
        str(raw),
        "--out-dir",
        str(out_dir),
        "--premise-kind",
        "hygiene",
    )
    h_m = hashlib.sha256((out_dir / "manifest.json").read_bytes()).hexdigest()
    h_d = hashlib.sha256((out_dir / "disposition.json").read_bytes()).hexdigest()
    review = out_dir / "disposition.md"
    review.write_text(
        review.read_text()
        + f"\nSIGN-OFF: approved HUMAN=operator manifest={h_m} disposition={h_d}\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE / "apply.py"),
            "--disposition",
            str(out_dir / "disposition.json"),
            "--review",
            str(out_dir / "disposition.md"),
            "--manifest",
            str(out_dir / "manifest.json"),
            "--memory-root",
            str(memory_root),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def advisory(memory_root: Path, threshold: int = 5) -> subprocess.CompletedProcess:
    return run_tool(
        ADVISORY, "--memory-root", str(memory_root), "--threshold", str(threshold)
    )


FORGET = {
    "repo/stale.md": {
        "verdict": "forget",
        "staleness": "expired",
        "staleness_evidence": "superseded",
    }
}


@pytest.mark.req("REQ-YG-622")
class TestMarker:
    def test_apply_writes_post_apply_baseline(self, memory_root, tmp_path):
        curate(memory_root, tmp_path / "out", FORGET)
        marker = json.loads((memory_root / ".curation-state.json").read_text())
        assert marker["version"] == 1
        assert "applied_at" in marker and "manifest_sha256" in marker
        assert "repo/stale.md" not in marker["notes"]  # forgotten path absent
        assert "repo/keepme.md" in marker["notes"]
        assert "repo/_tombstones.md" in marker["notes"]  # symmetric predicate

    def test_forget_run_yields_zero_immediate_drift(self, memory_root, tmp_path):
        curate(memory_root, tmp_path / "out", FORGET)
        result = advisory(memory_root, threshold=1)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == ""  # C-2: no false deleted-drift


@pytest.mark.req("REQ-YG-622")
class TestAdvisory:
    def test_silent_below_threshold(self, memory_root, tmp_path):
        curate(memory_root, tmp_path / "out", {})
        (memory_root / "repo" / "keepme.md").write_text("edited once\n")
        result = advisory(memory_root, threshold=5)
        assert result.returncode == 0 and result.stdout.strip() == ""

    def test_one_line_at_threshold(self, memory_root, tmp_path):
        curate(memory_root, tmp_path / "out", {})
        (memory_root / "repo" / "keepme.md").write_text("edited\n")
        (memory_root / "repo" / "new-note.md").write_text("new\n")
        result = advisory(memory_root, threshold=2)
        assert result.returncode == 0, result.stderr
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        assert len(lines) == 1
        assert "since last curation" in lines[0]

    def test_never_curated_non_empty_corpus(self, memory_root):
        result = advisory(memory_root)
        assert result.returncode == 0, result.stderr
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        assert len(lines) == 1
        assert "never curated" in lines[0]

    def test_deleted_notes_count_as_drift(self, memory_root, tmp_path):
        curate(memory_root, tmp_path / "out", {})
        (memory_root / "repo" / "keepme.md").unlink()
        (memory_root / "repo" / "stale.md").unlink()
        result = advisory(memory_root, threshold=2)
        assert result.returncode == 0, result.stderr
        assert "since last curation" in result.stdout

    def test_malformed_marker_is_a_real_error(self, memory_root):
        (memory_root / ".curation-state.json").write_text("{not json")
        result = advisory(memory_root)
        assert result.returncode != 0
        assert result.stderr.strip() != ""

    def test_no_provider_or_network_imports(self):
        source = ADVISORY.read_text()
        forbidden = (
            "requests",
            "httpx",
            "urllib",
            "socket",
            "langchain",
            "anthropic",
            "openai",
        )
        for name in forbidden:
            assert f"import {name}" not in source


@pytest.mark.req("REQ-YG-622")
class TestHookWrapper:
    def test_hook_fail_open_with_bounded_evidence(self, tmp_path):
        log = tmp_path / "advisory.jsonl"
        result = subprocess.run(
            ["sh", str(HOOK)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "MEMORY_ADVISORY_ROOT": str(tmp_path / "nonexistent"),
                "MEMORY_ADVISORY_LOG": str(log),
            },
        )
        assert result.returncode == 0
        record = json.loads(log.read_text().strip().splitlines()[-1])
        assert record["event"] == "memory_advisory_failed"

    def test_hook_prints_advisory_on_drift(self, memory_root, tmp_path):
        result = subprocess.run(
            ["sh", str(HOOK)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "MEMORY_ADVISORY_ROOT": str(memory_root),
                "MEMORY_ADVISORY_LOG": str(tmp_path / "advisory.jsonl"),
            },
        )
        assert result.returncode == 0
        assert "never curated" in result.stdout
