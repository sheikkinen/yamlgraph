"""Tests for the FR-875 memory-curation code stages (collect/reconcile/apply).

All tests use temporary memory roots and out-dirs (judgement C-5):
never the operator's real memory store.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
NODES = REPO_ROOT / "examples" / "memory-curation" / "nodes"
APPLY = REPO_ROOT / "examples" / "memory-curation" / "apply.py"


def run_tool(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        env={**os.environ},
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture()
def memory_root(tmp_path: Path) -> Path:
    root = tmp_path / "memories"
    (root / "repo").mkdir(parents=True)
    (root / "repo" / "keepme.md").write_text("# Durable fact\nstill true\n")
    (root / "repo" / "stale.md").write_text("# Version pin\nfoo is v0.1.7\n")
    root.joinpath("user-note.md").write_text("# User scope\nnot repo scope\n")
    return root


@pytest.fixture()
def out_dir(tmp_path: Path) -> Path:
    return tmp_path / "out"


def collect(memory_root: Path, out_dir: Path) -> subprocess.CompletedProcess:
    return run_tool(
        NODES / "collect.py",
        "--memory-root",
        str(memory_root),
        "--out-dir",
        str(out_dir),
    )


def make_disposition_rows(manifest: dict) -> list[dict]:
    rows = []
    for key in manifest["notes"]:
        rows.append(
            {
                "path": key,
                "verdict": "keep",
                "audience": "machine_local",
                "rationale": "durable boundary fact",
                "redacted_draft": None,
                "staleness": "fresh",
                "staleness_evidence": None,
            }
        )
    return rows


@pytest.mark.req("REQ-YG-620")
class TestCollect:
    def test_manifest_and_copies(self, memory_root, out_dir):
        result = collect(memory_root, out_dir)
        assert result.returncode == 0, result.stderr
        manifest = json.loads((out_dir / "manifest.json").read_text())
        assert set(manifest["notes"]) == {"repo/keepme.md", "repo/stale.md"}
        entry = manifest["notes"]["repo/keepme.md"]
        body = (memory_root / "repo" / "keepme.md").read_bytes()
        assert entry["sha256"] == sha256_bytes(body)
        assert entry["size"] == len(body)
        assert "mtime" in entry
        assert (out_dir / "notes" / "repo" / "keepme.md").read_bytes() == body

    def test_repo_scope_only(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        assert not any("user-note" in k for k in manifest["notes"])
        assert not (out_dir / "notes" / "user-note.md").exists()

    def test_rejects_symlink_escape(self, memory_root, out_dir, tmp_path):
        outside = tmp_path / "outside.md"
        outside.write_text("secret\n")
        (memory_root / "repo" / "evil.md").symlink_to(outside)
        result = collect(memory_root, out_dir)
        assert result.returncode != 0
        assert "symlink" in (result.stdout + result.stderr).lower()

    def test_writes_only_under_out_dir(self, memory_root, out_dir, tmp_path):
        before = set(tmp_path.rglob("*"))
        collect(memory_root, out_dir)
        new = set(tmp_path.rglob("*")) - before
        assert all(out_dir in p.parents or p == out_dir for p in new)


@pytest.mark.req("REQ-YG-620")
class TestReconcile:
    def _reconcile(
        self, out_dir: Path, rows: list[dict]
    ) -> subprocess.CompletedProcess:
        dispositions = out_dir / "raw-dispositions.json"
        dispositions.write_text(json.dumps(rows))
        return run_tool(
            NODES / "reconcile.py",
            "--manifest",
            str(out_dir / "manifest.json"),
            "--dispositions",
            str(dispositions),
            "--out-dir",
            str(out_dir),
        )

    def test_valid_rows_render_outputs(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        result = self._reconcile(out_dir, make_disposition_rows(manifest))
        assert result.returncode == 0, result.stderr
        disposition = json.loads((out_dir / "disposition.json").read_text())
        assert disposition["manifest_sha256"] == sha256_bytes(
            (out_dir / "manifest.json").read_bytes()
        )
        assert set(disposition["notes"]) == set(manifest["notes"])
        review = (out_dir / "disposition.md").read_text()
        assert "SIGN-OFF" in review

    def test_missing_note_fails(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        rows = make_disposition_rows(manifest)[:-1]
        result = self._reconcile(out_dir, rows)
        assert result.returncode != 0

    def test_unknown_path_fails(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        rows = make_disposition_rows(manifest)
        rows.append(dict(rows[0], path="repo/phantom.md"))
        result = self._reconcile(out_dir, rows)
        assert result.returncode != 0

    def test_duplicate_path_fails(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        rows = make_disposition_rows(manifest)
        rows.append(dict(rows[0]))
        result = self._reconcile(out_dir, rows)
        assert result.returncode != 0

    def test_unknown_verdict_fails(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        rows = make_disposition_rows(manifest)
        rows[0]["verdict"] = "maybe"
        result = self._reconcile(out_dir, rows)
        assert result.returncode != 0

    def test_redact_requires_draft(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        rows = make_disposition_rows(manifest)
        rows[0]["verdict"] = "redact"  # redacted_draft stays None
        result = self._reconcile(out_dir, rows)
        assert result.returncode != 0

    def test_dated_requires_evidence(self, memory_root, out_dir):
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        rows = make_disposition_rows(manifest)
        rows[0]["staleness"] = "dated"  # staleness_evidence stays None
        result = self._reconcile(out_dir, rows)
        assert result.returncode != 0


@pytest.mark.req("REQ-YG-620")
class TestApply:
    def _prepare(self, memory_root: Path, out_dir: Path, verdicts: dict) -> None:
        """Collect, reconcile with given per-note verdicts, sign off."""
        collect(memory_root, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        rows = make_disposition_rows(manifest)
        for row in rows:
            if row["path"] in verdicts:
                row.update(verdicts[row["path"]])
        dispositions = out_dir / "raw-dispositions.json"
        dispositions.write_text(json.dumps(rows))
        run_tool(
            NODES / "reconcile.py",
            "--manifest",
            str(out_dir / "manifest.json"),
            "--dispositions",
            str(dispositions),
            "--out-dir",
            str(out_dir),
            "--premise-kind",
            "hygiene",
        )

    def _sign(self, out_dir: Path) -> None:
        h_m = sha256_bytes((out_dir / "manifest.json").read_bytes())
        h_d = sha256_bytes((out_dir / "disposition.json").read_bytes())
        review = out_dir / "disposition.md"
        review.write_text(
            review.read_text()
            + f"\nSIGN-OFF: approved HUMAN=operator manifest={h_m} disposition={h_d}\n"
        )

    def _apply(self, memory_root: Path, out_dir: Path) -> subprocess.CompletedProcess:
        return run_tool(
            APPLY,
            "--disposition",
            str(out_dir / "disposition.json"),
            "--review",
            str(out_dir / "disposition.md"),
            "--manifest",
            str(out_dir / "manifest.json"),
            "--memory-root",
            str(memory_root),
        )

    FORGET_STALE = {
        "repo/stale.md": {
            "verdict": "forget",
            "staleness": "expired",
            "staleness_evidence": "pins foo v0.1.7; superseded",
        }
    }
    REDACT_KEEP = {
        "repo/keepme.md": {
            "verdict": "redact",
            "redacted_draft": "# Durable fact\nredacted body\n",
        }
    }

    def test_refuses_without_signoff(self, memory_root, out_dir):
        self._prepare(memory_root, out_dir, self.FORGET_STALE)
        result = self._apply(memory_root, out_dir)
        assert result.returncode != 0
        assert (memory_root / "repo" / "stale.md").exists()

    def test_refuses_wrong_hash_signoff(self, memory_root, out_dir):
        self._prepare(memory_root, out_dir, self.FORGET_STALE)
        review = out_dir / "disposition.md"
        review.write_text(
            review.read_text()
            + f"\nSIGN-OFF: approved HUMAN=operator manifest={'0' * 64} disposition={'0' * 64}\n"
        )
        result = self._apply(memory_root, out_dir)
        assert result.returncode != 0
        assert (memory_root / "repo" / "stale.md").exists()

    def test_signed_apply_executes_verdicts(self, memory_root, out_dir):
        self._prepare(memory_root, out_dir, {**self.FORGET_STALE, **self.REDACT_KEEP})
        self._sign(out_dir)
        result = self._apply(memory_root, out_dir)
        assert result.returncode == 0, result.stderr
        assert not (memory_root / "repo" / "stale.md").exists()
        assert (
            memory_root / "repo" / "keepme.md"
        ).read_text() == "# Durable fact\nredacted body\n"

    def test_idempotent_rerun(self, memory_root, out_dir):
        self._prepare(memory_root, out_dir, {**self.FORGET_STALE, **self.REDACT_KEEP})
        self._sign(out_dir)
        assert self._apply(memory_root, out_dir).returncode == 0
        result = self._apply(memory_root, out_dir)
        assert result.returncode == 0, result.stderr

    def test_refuses_on_live_drift(self, memory_root, out_dir):
        self._prepare(memory_root, out_dir, self.FORGET_STALE)
        self._sign(out_dir)
        (memory_root / "repo" / "stale.md").write_text("edited after collection\n")
        result = self._apply(memory_root, out_dir)
        assert result.returncode != 0
        assert "drift" in (result.stdout + result.stderr).lower()
        assert (
            memory_root / "repo" / "stale.md"
        ).read_text() == "edited after collection\n"

    def test_drift_anywhere_refuses_everything(self, memory_root, out_dir):
        self._prepare(memory_root, out_dir, {**self.FORGET_STALE, **self.REDACT_KEEP})
        self._sign(out_dir)
        (memory_root / "repo" / "keepme.md").write_text("edited after collection\n")
        result = self._apply(memory_root, out_dir)
        assert result.returncode != 0
        # no partial apply: stale.md must survive even though its own hash matched
        assert (memory_root / "repo" / "stale.md").exists()
