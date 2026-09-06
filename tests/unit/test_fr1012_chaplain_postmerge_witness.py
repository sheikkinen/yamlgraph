"""FR-1012 Step 3 — scripts/chaplain_postmerge_witness.sh fixture tests (REQ-YG-666, CAP-264).

A tiny git checkout with a fake `scripts/vscode/now.py`; sync is skipped via the test hook.
POSIX shell tests: BASH_BIN selects the shell.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "chaplain_postmerge_witness.sh"
BASH = os.environ.get("BASH_BIN", "bash")

pytestmark = pytest.mark.process


def _git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "scripts" / "vscode").mkdir(parents=True)
    (root / "docs" / "census").mkdir(parents=True)
    (root / "tmp").mkdir()
    shutil.copy(SCRIPT, root / "scripts" / "chaplain_postmerge_witness.sh")
    (root / "scripts" / "vscode" / "now.py").write_text('print("now: nothing about the old runtime")\n', encoding="utf-8")
    (root / "live.txt").write_text("live\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "clean tree")
    return root


def run(root: Path, extra_env=None):
    env = {**os.environ, "CHAPLAIN_WITNESS_SKIP_SYNC": "1", **(extra_env or {})}
    return subprocess.run([BASH, "scripts/chaplain_postmerge_witness.sh", "--out", "docs/census/chaplain-postmerge.run.json"], cwd=root, env=env, capture_output=True, text=True)


def record(root: Path) -> dict:
    return json.loads((root / "docs/census/chaplain-postmerge.run.json").read_text(encoding="utf-8"))


@pytest.mark.req("REQ-YG-666")
def test_clean_tree_passes_and_records(repo):
    r = run(repo)
    assert r.returncode == 0, r.stderr + r.stdout
    rec = record(repo)
    assert rec["all_checks_pass"] is True and rec["git_ls_files_chaplain"] == [] and rec["now_py_mentions_chaplain"] is False
    assert rec["worktree_sync"] == "skipped" and rec["prerequisites"]["FR-1015"] == "32fd6e9f" and len(rec["main_head"]) == 40


@pytest.mark.req("REQ-YG-666")
def test_tracked_chaplain_file_fails_with_65_but_still_records(repo):
    (repo / ".chaplain").mkdir()
    (repo / ".chaplain" / "left.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "runtime still tracked")
    r = run(repo)
    assert r.returncode == 65
    rec = record(repo)
    assert rec["git_ls_files_chaplain"] == [".chaplain/left.txt"] and rec["all_checks_pass"] is False


@pytest.mark.req("REQ-YG-666")
def test_now_py_mentioning_chaplain_fails_with_65(repo):
    (repo / "scripts" / "vscode" / "now.py").write_text('print("refresh: yamlgraph graph run .chaplain/graphs/x.yaml")\n', encoding="utf-8")
    r = run(repo)
    assert r.returncode == 65
    assert record(repo)["now_py_mentions_chaplain"] is True
