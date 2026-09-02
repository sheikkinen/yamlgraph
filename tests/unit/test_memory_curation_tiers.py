"""Tests for FR-878: reversible amnesia (archive/restore/tombstones) and
tiered approval in the memory-curation apply stage.

All tests use temporary memory roots (judgement C-3).
"""

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


def run_tool(
    script: Path, *args: str, env: dict | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


@pytest.fixture()
def memory_root(tmp_path: Path) -> Path:
    root = tmp_path / "memories"
    (root / "repo").mkdir(parents=True)
    (root / "repo" / "keepme.md").write_text("# Durable\nstill true\n", encoding="utf-8")
    (root / "repo" / "stale.md").write_text("# Pin\nfoo v0.1.7\n", encoding="utf-8")
    return root


@pytest.fixture()
def out_dir(tmp_path: Path) -> Path:
    return tmp_path / "out"


def pipeline(
    memory_root: Path,
    out_dir: Path,
    verdicts: dict,
    premise_kind: str | None = "hygiene",
) -> None:
    """collect -> build rows -> reconcile (with premise kind)."""
    run_tool(
        NODES / "collect.py",
        "--memory-root",
        str(memory_root),
        "--out-dir",
        str(out_dir),
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
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
    raw.write_text(json.dumps(rows), encoding="utf-8")
    args = [
        "--manifest",
        str(out_dir / "manifest.json"),
        "--dispositions",
        str(raw),
        "--out-dir",
        str(out_dir),
    ]
    if premise_kind:
        args += ["--premise-kind", premise_kind]
    result = run_tool(NODES / "reconcile.py", *args)
    assert result.returncode == 0, result.stderr


def sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def sign(out_dir: Path, extra: str = "") -> None:
    h_m = sha256_bytes((out_dir / "manifest.json").read_bytes())
    h_d = sha256_bytes((out_dir / "disposition.json").read_bytes())
    review = out_dir / "disposition.md"
    review.write_text(
        review.read_text(encoding="utf-8")
        + f"\nSIGN-OFF: approved {extra} manifest={h_m} disposition={h_d}\n"
    , encoding="utf-8")


def apply_run(
    memory_root: Path, out_dir: Path, env: dict | None = None
) -> subprocess.CompletedProcess:
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
        env=env,
    )


FORGET = {
    "repo/stale.md": {
        "verdict": "forget",
        "staleness": "expired",
        "staleness_evidence": "pin superseded",
    }
}
REDACT = {
    "repo/keepme.md": {"verdict": "redact", "redacted_draft": "# Durable\ncompressed\n"}
}


@pytest.mark.req("REQ-YG-621")
class TestArchive:
    def test_forget_archives_and_tombstones(self, memory_root, out_dir, tmp_path):
        pipeline(memory_root, out_dir, FORGET)
        sign(out_dir, "HUMAN=operator")
        result = apply_run(memory_root, out_dir)
        assert result.returncode == 0, result.stderr
        assert not (memory_root / "repo" / "stale.md").exists()
        archived = list((memory_root / ".archive").rglob("stale.md"))
        assert len(archived) == 1
        assert archived[0].read_text(encoding="utf-8") == "# Pin\nfoo v0.1.7\n"
        rows = (memory_root / "repo" / "_tombstones.md").read_text(encoding="utf-8")
        assert "repo/stale.md" in rows and "forget" in rows

    def test_redact_stashes_original_as_backup(self, memory_root, out_dir):
        pipeline(memory_root, out_dir, REDACT)
        sign(out_dir, "DELEGATION: FR-878 tier-1 standing (operator 2026-08-24)")
        result = apply_run(memory_root, out_dir)
        assert result.returncode == 0, result.stderr
        archived = list((memory_root / ".archive").rglob("keepme.md"))
        assert len(archived) == 1
        assert archived[0].read_text(encoding="utf-8") == "# Durable\nstill true\n"
        assert "redact-backup" in (memory_root / "repo" / "_tombstones.md").read_text(encoding="utf-8")

    def test_archive_excluded_from_collect(self, memory_root, out_dir, tmp_path):
        pipeline(memory_root, out_dir, FORGET)
        sign(out_dir, "HUMAN=operator")
        apply_run(memory_root, out_dir)
        out2 = tmp_path / "out2"
        run_tool(
            NODES / "collect.py",
            "--memory-root",
            str(memory_root),
            "--out-dir",
            str(out2),
        )
        manifest = json.loads((out2 / "manifest.json").read_text(encoding="utf-8"))
        assert not any(".archive" in k for k in manifest["notes"])

    def test_tombstone_file_is_protected(self, memory_root, out_dir):
        (memory_root / "repo" / "_tombstones.md").write_text("op | seed row\n", encoding="utf-8")
        pipeline(
            memory_root,
            out_dir,
            {
                "repo/_tombstones.md": {
                    "verdict": "forget",
                    "staleness": "expired",
                    "staleness_evidence": "x",
                }
            },
        )
        sign(out_dir, "HUMAN=operator")
        result = apply_run(memory_root, out_dir)
        assert result.returncode != 0
        assert (memory_root / "repo" / "_tombstones.md").exists()


@pytest.mark.req("REQ-YG-621")
class TestTiers:
    def test_tier0_keep_only_needs_no_signoff(self, memory_root, out_dir):
        pipeline(memory_root, out_dir, {})
        result = apply_run(memory_root, out_dir)
        assert result.returncode == 0, result.stderr

    def test_tier1_redact_accepts_delegation_and_audits(
        self, memory_root, out_dir, tmp_path
    ):
        audit = tmp_path / "audit.jsonl"
        pipeline(memory_root, out_dir, REDACT)
        sign(out_dir, "DELEGATION: FR-878 tier-1 standing (operator 2026-08-24)")
        result = apply_run(
            memory_root, out_dir, env={"MEMORY_CURATION_AUDIT_LOG": str(audit)}
        )
        assert result.returncode == 0, result.stderr
        record = json.loads(audit.read_text(encoding="utf-8").strip().splitlines()[-1])
        assert record["tier"] == 1

    def test_tier1_refuses_plain_signoff(self, memory_root, out_dir):
        pipeline(memory_root, out_dir, REDACT)
        sign(out_dir)
        assert apply_run(memory_root, out_dir).returncode != 0

    def test_tier2_forget_refuses_delegation(self, memory_root, out_dir):
        pipeline(memory_root, out_dir, FORGET)
        sign(out_dir, "DELEGATION: FR-878 tier-1 standing (operator 2026-08-24)")
        result = apply_run(memory_root, out_dir)
        assert result.returncode != 0
        assert (memory_root / "repo" / "stale.md").exists()

    def test_tier2_forget_requires_human(self, memory_root, out_dir):
        pipeline(memory_root, out_dir, FORGET)
        sign(out_dir, "HUMAN=operator")
        assert apply_run(memory_root, out_dir).returncode == 0

    def test_tier3_export_premise_needs_explicit_ack(self, memory_root, out_dir):
        pipeline(memory_root, out_dir, REDACT, premise_kind="export_publication")
        sign(out_dir, "HUMAN=operator")
        assert apply_run(memory_root, out_dir).returncode != 0
        pipeline(memory_root, out_dir, REDACT, premise_kind="export_publication")
        sign(out_dir, "HUMAN=operator EXPORT_PUBLICATION_APPROVED")
        assert apply_run(memory_root, out_dir).returncode == 0

    def test_missing_premise_kind_fails_closed_to_tier3(self, memory_root, out_dir):
        pipeline(memory_root, out_dir, REDACT, premise_kind=None)
        sign(out_dir, "DELEGATION: FR-878 tier-1 standing (operator 2026-08-24)")
        assert apply_run(memory_root, out_dir).returncode != 0


@pytest.mark.req("REQ-YG-621")
class TestRestore:
    def _forget_and_get_archive(self, memory_root, out_dir) -> str:
        pipeline(memory_root, out_dir, FORGET)
        sign(out_dir, "HUMAN=operator")
        assert apply_run(memory_root, out_dir).returncode == 0
        archived = list((memory_root / ".archive").rglob("stale.md"))
        return str(archived[0].relative_to(memory_root / ".archive"))

    def test_restore_returns_note_and_records(self, memory_root, out_dir):
        ref = self._forget_and_get_archive(memory_root, out_dir)
        result = run_tool(APPLY, "restore", ref, "--memory-root", str(memory_root))
        assert result.returncode == 0, result.stderr
        assert (memory_root / "repo" / "stale.md").read_text(encoding="utf-8") == "# Pin\nfoo v0.1.7\n"
        assert "restored" in (memory_root / "repo" / "_tombstones.md").read_text(encoding="utf-8")

    def test_restore_idempotent_when_recorded(self, memory_root, out_dir):
        ref = self._forget_and_get_archive(memory_root, out_dir)
        run_tool(APPLY, "restore", ref, "--memory-root", str(memory_root))
        result = run_tool(APPLY, "restore", ref, "--memory-root", str(memory_root))
        assert result.returncode == 0, result.stderr

    def test_restore_conflict_on_diverged_live_file(self, memory_root, out_dir):
        ref = self._forget_and_get_archive(memory_root, out_dir)
        (memory_root / "repo" / "stale.md").write_text("new unrelated note\n", encoding="utf-8")
        result = run_tool(APPLY, "restore", ref, "--memory-root", str(memory_root))
        assert result.returncode != 0
        assert "conflict" in (result.stdout + result.stderr).lower()
        assert (memory_root / "repo" / "stale.md").read_text(encoding="utf-8") == "new unrelated note\n"


@pytest.mark.req("REQ-YG-621")
class TestRederivation:
    def test_recreated_forgotten_note_triggers_advisory(
        self, memory_root, out_dir, tmp_path
    ):
        pipeline(memory_root, out_dir, FORGET)
        sign(out_dir, "HUMAN=operator")
        apply_run(memory_root, out_dir)
        (memory_root / "repo" / "stale.md").write_text("re-derived lesson\n", encoding="utf-8")
        result = run_tool(
            NODES / "collect.py",
            "--memory-root",
            str(memory_root),
            "--out-dir",
            str(tmp_path / "o2"),
        )
        assert result.returncode == 0, result.stderr
        assert "resembles archived" in result.stdout

    def test_redaction_backup_never_triggers_advisory(
        self, memory_root, out_dir, tmp_path
    ):
        pipeline(memory_root, out_dir, REDACT)
        sign(out_dir, "DELEGATION: FR-878 tier-1 standing (operator 2026-08-24)")
        apply_run(memory_root, out_dir)
        result = run_tool(
            NODES / "collect.py",
            "--memory-root",
            str(memory_root),
            "--out-dir",
            str(tmp_path / "o2"),
        )
        assert result.returncode == 0, result.stderr
        assert "resembles archived" not in result.stdout
