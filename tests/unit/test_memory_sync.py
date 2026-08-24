"""Tests for scripts/memory_sync.py — FR-874 cross-device agent memory sync.

All tests use temporary memory-tool roots and stores (judgement C-3):
never the operator's real VS Code memory directories.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "memory_sync.py"


def run_sync(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = {**os.environ, "YAMLGRAPH_AGENT_MEMORY_ROOT": ""}
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


@pytest.fixture()
def memory_root(tmp_path: Path) -> Path:
    root = tmp_path / "memories"
    (root / "repo").mkdir(parents=True)
    (root / "repo" / "fact.md").write_text("# Repo fact\nboundary detail\n")
    root.joinpath("practice.md").write_text("# User practice\nnot promoted\n")
    return root


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    return tmp_path / "agent-memory"


def manifest_of(store: Path) -> dict:
    return json.loads((store / "manifest.json").read_text())


@pytest.mark.req("REQ-YG-620")
class TestExport:
    def test_export_repo_notes_and_manifest(self, memory_root, store):
        result = run_sync(
            "export", "--memory-root", str(memory_root), "--store", str(store)
        )
        assert result.returncode == 0, result.stderr
        assert (
            store / "repo" / "fact.md"
        ).read_text() == "# Repo fact\nboundary detail\n"
        manifest = manifest_of(store)
        entry = manifest["notes"]["repo/fact.md"]
        assert entry["scope"] == "repo"
        assert len(entry["sha256"]) == 64

    def test_export_never_exports_unpromoted_user_notes(self, memory_root, store):
        result = run_sync(
            "export", "--memory-root", str(memory_root), "--store", str(store)
        )
        assert result.returncode == 0, result.stderr
        assert not (store / "shared" / "practice.md").exists()
        assert "shared/practice.md" not in manifest_of(store)["notes"]

    def test_promote_then_export_includes_shared(self, memory_root, store):
        result = run_sync(
            "promote",
            "practice.md",
            "--memory-root",
            str(memory_root),
            "--store",
            str(store),
        )
        assert result.returncode == 0, result.stderr
        result = run_sync(
            "export", "--memory-root", str(memory_root), "--store", str(store)
        )
        assert result.returncode == 0, result.stderr
        assert (
            store / "shared" / "practice.md"
        ).read_text() == "# User practice\nnot promoted\n"
        entry = manifest_of(store)["notes"]["shared/practice.md"]
        assert entry["scope"] == "user"
        assert entry["promoted_from"] == "practice.md"


@pytest.mark.req("REQ-YG-620")
class TestImportRoundtrip:
    def test_export_wipe_import_reproduces_bytes(self, memory_root, store, tmp_path):
        run_sync("export", "--memory-root", str(memory_root), "--store", str(store))
        fresh = tmp_path / "fresh-memories"
        fresh.mkdir()
        result = run_sync("import", "--memory-root", str(fresh), "--store", str(store))
        assert result.returncode == 0, result.stderr
        assert (
            fresh / "repo" / "fact.md"
        ).read_text() == "# Repo fact\nboundary detail\n"
        base = json.loads((fresh / ".import-base.json").read_text())
        assert (
            base["repo/fact.md"]
            == manifest_of(store)["notes"]["repo/fact.md"]["sha256"]
        )


@pytest.mark.req("REQ-YG-620")
class TestImportConflicts:
    def _sync_two_roots(self, memory_root, store, tmp_path):
        """Export from root A, import into root B; return B."""
        run_sync("export", "--memory-root", str(memory_root), "--store", str(store))
        other = tmp_path / "other-memories"
        other.mkdir()
        run_sync("import", "--memory-root", str(other), "--store", str(store))
        return other

    def test_conflict_refused_without_force(self, memory_root, store, tmp_path):
        other = self._sync_two_roots(memory_root, store, tmp_path)
        # both sides diverge from the recorded base
        (other / "repo" / "fact.md").write_text("local divergence\n")
        (memory_root / "repo" / "fact.md").write_text("remote divergence\n")
        run_sync("export", "--memory-root", str(memory_root), "--store", str(store))
        result = run_sync("import", "--memory-root", str(other), "--store", str(store))
        assert result.returncode != 0
        assert "conflict" in (result.stdout + result.stderr).lower()
        assert (other / "repo" / "fact.md").read_text() == "local divergence\n"

    def test_force_overwrites_and_records_new_base(self, memory_root, store, tmp_path):
        other = self._sync_two_roots(memory_root, store, tmp_path)
        (other / "repo" / "fact.md").write_text("local divergence\n")
        (memory_root / "repo" / "fact.md").write_text("remote divergence\n")
        run_sync("export", "--memory-root", str(memory_root), "--store", str(store))
        result = run_sync(
            "import", "--memory-root", str(other), "--store", str(store), "--force"
        )
        assert result.returncode == 0, result.stderr
        assert (other / "repo" / "fact.md").read_text() == "remote divergence\n"
        base = json.loads((other / ".import-base.json").read_text())
        assert (
            base["repo/fact.md"]
            == manifest_of(store)["notes"]["repo/fact.md"]["sha256"]
        )

    def test_local_ahead_keeps_local_without_error(self, memory_root, store, tmp_path):
        other = self._sync_two_roots(memory_root, store, tmp_path)
        (other / "repo" / "fact.md").write_text("local progress\n")
        result = run_sync("import", "--memory-root", str(other), "--store", str(store))
        assert result.returncode == 0, result.stderr
        assert (other / "repo" / "fact.md").read_text() == "local progress\n"


@pytest.mark.req("REQ-YG-620")
class TestSanitization:
    @pytest.mark.parametrize(
        "bad_key",
        ["repo/../evil.md", "/etc/evil.md", "repo/evil.txt", "repo/sub/dir.md"],
    )
    def test_import_rejects_malformed_manifest_paths(self, store, tmp_path, bad_key):
        store.mkdir(parents=True)
        (store / "manifest.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "notes": {
                        bad_key: {
                            "scope": "repo",
                            "sha256": "0" * 64,
                            "promoted_from": None,
                        }
                    },
                    "promoted": [],
                }
            )
        )
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        result = run_sync("import", "--memory-root", str(fresh), "--store", str(store))
        assert result.returncode != 0
        assert not (tmp_path / "evil.md").exists()
        assert not list(fresh.rglob("*.md"))

    def test_promote_rejects_traversal_name(self, memory_root, store):
        result = run_sync(
            "promote",
            "../outside.md",
            "--memory-root",
            str(memory_root),
            "--store",
            str(store),
        )
        assert result.returncode != 0


@pytest.mark.req("REQ-YG-620")
class TestSubrepoDiscovery:
    def test_env_var_discovery_import_works(self, memory_root, store, tmp_path):
        run_sync("export", "--memory-root", str(memory_root), "--store", str(store))
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        result = run_sync(
            "import",
            "--memory-root",
            str(fresh),
            env={"YAMLGRAPH_AGENT_MEMORY_ROOT": str(store)},
        )
        assert result.returncode == 0, result.stderr
        assert (fresh / "repo" / "fact.md").exists()

    def test_env_var_store_is_readonly_export_refused(self, memory_root, store):
        run_sync("export", "--memory-root", str(memory_root), "--store", str(store))
        result = run_sync(
            "export",
            "--memory-root",
            str(memory_root),
            env={"YAMLGRAPH_AGENT_MEMORY_ROOT": str(store)},
        )
        assert result.returncode != 0
        assert "read-only" in (result.stdout + result.stderr).lower()

    def test_invalid_env_var_errors_observably(self, tmp_path):
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        result = run_sync(
            "import",
            "--memory-root",
            str(fresh),
            env={"YAMLGRAPH_AGENT_MEMORY_ROOT": str(tmp_path / "nonexistent")},
        )
        assert result.returncode != 0
        assert "YAMLGRAPH_AGENT_MEMORY_ROOT" in (result.stdout + result.stderr)


@pytest.mark.req("REQ-YG-620")
class TestSessionStartHook:
    """AC-08: hook wrapper is fail-open but leaves bounded audit evidence."""

    HOOK = REPO_ROOT / ".github" / "hooks" / "scripts" / "memory-import.sh"

    def test_hook_exits_zero_on_broken_store_and_writes_audit(self, tmp_path):
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        log = tmp_path / "memory-sync.jsonl"
        result = subprocess.run(
            ["sh", str(self.HOOK)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "MEMORY_SYNC_ROOT": str(fresh),
                "MEMORY_SYNC_STORE": str(tmp_path / "missing-store"),
                "MEMORY_SYNC_LOG": str(log),
            },
        )
        assert result.returncode == 0
        lines = log.read_text().strip().splitlines()
        assert len(lines) >= 1
        record = json.loads(lines[-1])
        assert record["event"] == "memory_sync_import_failed"

    def test_hook_exits_zero_on_success(self, memory_root, store, tmp_path):
        run_sync("export", "--memory-root", str(memory_root), "--store", str(store))
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        log = tmp_path / "memory-sync.jsonl"
        result = subprocess.run(
            ["sh", str(self.HOOK)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "MEMORY_SYNC_ROOT": str(fresh),
                "MEMORY_SYNC_STORE": str(store),
                "MEMORY_SYNC_LOG": str(log),
            },
        )
        assert result.returncode == 0
        assert (fresh / "repo" / "fact.md").exists()
