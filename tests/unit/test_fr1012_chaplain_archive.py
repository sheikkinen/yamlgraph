"""FR-1012 Step 1 — scripts/chaplain_archive.sh fixture tests (REQ-YG-666, CAP-264).

A bare "origin", a bare "archive" remote and a fake `gh` stand in for GitHub. Covers:
dry run (no journal, manifest from the commit object, archive-relative paths), the
full journaled run, every typed refusal (64 usage, 65 tag collision, 66 repo
collision, 67 PRE not on origin/main, 69 resume mismatch), and partial-failure
resume without duplicate mutation. POSIX shell tests: BASH_BIN selects the shell.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "chaplain_archive.sh"
BASH = os.environ.get("BASH_BIN", "bash")

pytestmark = pytest.mark.process

FAKE_GH = r'''#!/usr/bin/env bash
# fake gh: state lives in $FAKE_GH_STATE
set -e
state="$FAKE_GH_STATE"; mkdir -p "$state"
cmd="$1 $2"; shift 2
case "$cmd" in
  "repo view")
    repo="$1"; shift
    [ -f "$state/$(basename "$repo").created" ] || { echo "GraphQL: Could not resolve to a Repository" >&2; exit 1; }
    case "$*" in
      *visibility*) cat "$state/$(basename "$repo").visibility" ;;
      *isArchived*) [ -f "$state/$(basename "$repo").archived" ] && echo true || echo false ;;
      *) echo '{"name":"x"}' ;;
    esac ;;
  "repo create")
    repo="$1"; shift
    touch "$state/$(basename "$repo").created"
    case "$*" in *--private*) echo PRIVATE > "$state/$(basename "$repo").visibility" ;; *--public*) echo PUBLIC > "$state/$(basename "$repo").visibility" ;; esac
    echo "created $repo $*" >> "$state/calls.log" ;;
  "repo archive")
    repo="$1"; touch "$state/$(basename "$repo").archived"; echo "archived $repo" >> "$state/calls.log" ;;
  *) echo "fake gh: unsupported $cmd" >&2; exit 2 ;;
esac
'''


def _git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def world(tmp_path: Path):
    origin = tmp_path / "origin.git"
    archive = tmp_path / "archive.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(archive)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True, capture_output=True)
    _git(repo, "checkout", "-q", "-b", "main")
    (repo / ".chaplain" / "scripts").mkdir(parents=True)
    (repo / ".chaplain" / "README.md").write_text("# Chaplain\n\nruntime docs\n", encoding="utf-8")
    (repo / ".chaplain" / "scripts" / "start-system.sh").write_text("#!/bin/bash\ncd ../..\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    shutil.copy(SCRIPT, repo / "scripts" / "chaplain_archive.sh")
    (repo / "yamlgraph.txt").write_text("live\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "pre-census tree")
    pre = _git(repo, "rev-parse", "HEAD")
    (repo / "docs" / "census").mkdir(parents=True)
    (repo / "docs" / "census" / "chaplain-disposition-input.jsonl").write_text(json.dumps({"source_sha": pre, "path": ".chaplain/README.md", "kind": "test"}) + "\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "census evidence")
    evidence = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "-q", "-u", "origin", "main")
    gh = tmp_path / "gh"
    gh.write_text(FAKE_GH, encoding="utf-8")
    gh.chmod(0o755)
    env = {**os.environ, "CHAPLAIN_ARCHIVE_GH": str(gh), "CHAPLAIN_ARCHIVE_REMOTE": str(archive), "FAKE_GH_STATE": str(tmp_path / "ghstate")}
    return {"repo": repo, "origin": origin, "archive": archive, "pre": evidence, "env": env, "state": tmp_path / "ghstate"}


def run(w, *args, extra_env=None):
    env = {**w["env"], **(extra_env or {})}
    return subprocess.run([BASH, "scripts/chaplain_archive.sh", *args], cwd=w["repo"], env=env, capture_output=True, text=True)


def journal(w) -> dict:
    return json.loads((w["repo"] / "docs/census/chaplain-archive.run.json").read_text(encoding="utf-8"))


@pytest.mark.req("REQ-YG-666")
def test_usage_refusals(world):
    assert run(world, "--pre", world["pre"]).returncode == 64
    assert run(world, "--visibility", "secret", "--pre", world["pre"]).returncode == 64
    assert run(world, "--visibility", "private").returncode == 64


@pytest.mark.req("REQ-YG-666")
def test_dry_run_writes_manifest_only(world):
    r = run(world, "--visibility", "private", "--pre", world["pre"], "--dry-run")
    assert r.returncode == 0, r.stderr
    assert "DRY RUN" in r.stdout and "gh repo create" not in (world["state"] / "calls.log").read_text() if (world["state"] / "calls.log").exists() else True
    manifest = (world["repo"] / "docs/census/chaplain-archive-manifest.txt").read_text(encoding="utf-8").splitlines()
    paths = [line.split("  ", 1)[1] for line in manifest]
    assert paths == ["README.md", "scripts/start-system.sh"], "paths must be archive-relative and sorted"
    assert not (world["repo"] / "docs/census/chaplain-archive.run.json").exists()
    assert not subprocess.run(["git", "ls-remote", "--tags", str(world["origin"])], capture_output=True, text=True).stdout


@pytest.mark.req("REQ-YG-666")
def test_full_run_journals_every_transition_and_archives(world):
    (world["repo"] / "docs/census/chaplain-archive-manifest.txt").unlink(missing_ok=True)
    r = run(world, "--visibility", "private", "--pre", world["pre"])
    assert r.returncode == 0, r.stderr + r.stdout
    j = journal(world)
    assert j["state"] == "archived" and j["pre"] == world["pre"] and j["visibility"] == "private"
    assert [t["state"] for t in j["transitions"]] == ["initialized", "tag_created", "repo_created", "split_pushed", "readme_committed", "verified", "archived"]
    tag = subprocess.run(["git", "ls-remote", "--tags", str(world["origin"]), "refs/tags/chaplain-archive"], capture_output=True, text=True).stdout.split()
    assert tag and tag[0] == world["pre"]
    readme = subprocess.run(["git", "--git-dir", str(world["archive"]), "show", "main:README.md"], capture_output=True, text=True).stdout
    assert "not a runnable distribution" in readme.splitlines()[0] and "runtime docs" in readme
    files = subprocess.run(["git", "--git-dir", str(world["archive"]), "ls-tree", "-r", "--name-only", "main"], capture_output=True, text=True).stdout.split()
    assert sorted(files) == ["README.md", "scripts/start-system.sh"], "archive root is the .chaplain subtree, nothing else"
    calls = (world["state"] / "calls.log").read_text()
    assert calls.count("created") == 1 and calls.count("archived") == 1


@pytest.mark.req("REQ-YG-666")
def test_partial_failure_then_resume_without_duplicate_mutation(world):
    r = run(world, "--visibility", "private", "--pre", world["pre"], extra_env={"CHAPLAIN_ARCHIVE_FAIL_AFTER": "repo_created"})
    assert r.returncode == 99 and journal(world)["state"] == "repo_created"
    # a plain re-run without --resume must refuse: the journal exists (69) or the tag/repo collide (65/66)
    assert run(world, "--visibility", "private", "--pre", world["pre"]).returncode in (65, 66, 69)
    r2 = run(world, "--visibility", "private", "--pre", world["pre"], "--resume")
    assert r2.returncode == 0, r2.stderr + r2.stdout
    assert journal(world)["state"] == "archived"
    assert (world["state"] / "calls.log").read_text().count("created") == 1, "repo must not be created twice"


@pytest.mark.req("REQ-YG-666")
def test_resume_refuses_mismatched_journal(world):
    run(world, "--visibility", "private", "--pre", world["pre"], extra_env={"CHAPLAIN_ARCHIVE_FAIL_AFTER": "tag_created"})
    j = journal(world)
    j["visibility"] = "public"
    (world["repo"] / "docs/census/chaplain-archive.run.json").write_text(json.dumps(j), encoding="utf-8")
    assert run(world, "--visibility", "private", "--pre", world["pre"], "--resume").returncode == 69


@pytest.mark.req("REQ-YG-666")
def test_tag_collision_at_other_commit_is_refused(world):
    other = _git(world["repo"], "rev-parse", "HEAD~1")
    _git(world["repo"], "tag", "chaplain-archive", other)
    _git(world["repo"], "push", "-q", "origin", "refs/tags/chaplain-archive")
    assert run(world, "--visibility", "private", "--pre", world["pre"], "--dry-run").returncode == 65


@pytest.mark.req("REQ-YG-666")
def test_existing_repo_without_journal_is_refused(world):
    world["state"].mkdir(exist_ok=True)
    (world["state"] / "yamlgraph-chaplain.created").touch()
    assert run(world, "--visibility", "private", "--pre", world["pre"], "--dry-run").returncode == 66


@pytest.mark.req("REQ-YG-666")
def test_pre_must_be_on_origin_main_and_match_the_input_tree(world):
    (world["repo"] / "yamlgraph.txt").write_text("changed\n", encoding="utf-8")
    _git(world["repo"], "commit", "-qam", "unpushed")
    unpushed = _git(world["repo"], "rev-parse", "HEAD")
    assert run(world, "--visibility", "private", "--pre", unpushed, "--dry-run").returncode == 67
    _git(world["repo"], "reset", "-q", "--hard", "origin/main")
    # a commit on origin/main whose .chaplain tree differs from the manifest's source tree
    (world["repo"] / ".chaplain" / "extra.txt").write_text("x\n", encoding="utf-8")
    _git(world["repo"], "add", "-A")
    _git(world["repo"], "commit", "-qm", "drift")
    _git(world["repo"], "push", "-q", "origin", "main")
    assert run(world, "--visibility", "private", "--pre", _git(world["repo"], "rev-parse", "HEAD"), "--dry-run").returncode == 67
