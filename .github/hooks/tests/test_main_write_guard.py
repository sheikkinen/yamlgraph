#!/usr/bin/env python3
"""Tests for the FR-888 main-write guard — worktree as the only enforcement
write path.

Covers: deny edit-tool writes to enforcement-class paths on the main
checkout (AC-01); allow the identical write in a linked worktree (AC-01);
docs-lane allowance (AC-02); git-plumbing worktree detection incl. nested
repos and parse errors (AC-03); terminal write grammar (AC-06/AC-08);
escape hatch audit (AC-07); worktree.sh .env + final cd line (AC-05) and
safe removal (AC-11).

Infrastructure test scope (FR-436): outside REQ-YG marker coverage.

Run:  pytest .github/hooks/tests/test_main_write_guard.py -q --no-cov
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "pre-command-guard.sh"
WORKTREE_SH = Path(__file__).resolve().parents[3] / "scripts" / "worktree.sh"
GIT = shutil.which("git") or "/usr/bin/git"
pytestmark = pytest.mark.req("REQ-YG-527")


def run_hook(payload, *, env_extra=None, log_dir=None, guard_root=None):
    env = {**os.environ}
    env.pop("FR888_ALLOW_MAIN", None)
    env.pop("YAMLGRAPH_AUTHORING_TOKEN", None)
    if env_extra:
        env.update(env_extra)
    if log_dir:
        env["HOOK_LOG_DIR"] = str(log_dir)
    if guard_root:
        env["HOOK_GUARD_ROOT"] = str(guard_root)
    r = subprocess.run(
        [str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return r.returncode, r.stdout.strip()


def decision_of(stdout: str) -> str:
    d = json.loads(stdout)
    if d.get("decision") == "approve":
        return "approve"
    return d.get("hookSpecificOutput", {}).get("permissionDecision", "unknown")


def reason_of(stdout: str) -> str:
    d = json.loads(stdout)
    return d.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")


def _git(cwd, *args):
    subprocess.run([GIT, *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    """Fixture main checkout + linked worktree + nested foreign repo."""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    for d in ("yamlgraph", "tests", "docs", "feature-requests"):
        (main / d).mkdir()
        (main / d / ".keep").write_text("")
    _git(main, "add", "-A")
    _git(main, "commit", "-m", "init")
    wt = tmp_path / "wt"
    _git(main, "worktree", "add", str(wt), "-b", "feat/x", "main")
    nested = main / "projects" / "foreign"
    nested.mkdir(parents=True)
    _git(nested, "init", "-b", "main")
    (nested / "yamlgraph").mkdir()
    return {"main": main, "wt": wt, "nested": nested}


def edit_payload(file_path, cwd):
    return {
        "tool_name": "create_file",
        "tool_input": {"filePath": str(file_path)},
        "session_id": "s888",
        "cwd": str(cwd),
    }


def terminal_payload(command, cwd):
    return {
        "tool_name": "run_in_terminal",
        "tool_input": {"command": command},
        "session_id": "s888",
        "cwd": str(cwd),
    }


# ── AC-01: edit-tool deny on main, allow in worktree ─────────────────


def test_edit_write_to_enforcement_path_on_main_denied(repo):
    _, out = run_hook(
        edit_payload(repo["main"] / "yamlgraph" / "x.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"
    assert "worktree.sh new" in reason_of(out)  # denial carries the cure


def test_identical_write_in_linked_worktree_allowed(repo):
    _, out = run_hook(
        edit_payload(repo["wt"] / "yamlgraph" / "x.py", repo["wt"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


# ── AC-02: docs lane always allowed on main ──────────────────────────


@pytest.mark.parametrize("lane", ["docs", "feature-requests"])
def test_docs_lane_on_main_allowed(repo, lane):
    _, out = run_hook(
        edit_payload(repo["main"] / lane / "note.md", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


# ── AC-03: plumbing detection — nested repo, parse error ─────────────


def test_nested_repo_not_misclassified_as_main_checkout(repo):
    # review PR#476 round 3 P1: a nested FOREIGN repo is not ours to
    # police — the guard protects the guard-root repository only
    _, out = run_hook(
        edit_payload(repo["nested"] / "yamlgraph" / "x.py", repo["nested"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


def test_apply_patch_delete_hunk_on_main_denied(repo):
    # review PR#476 round 3 P2: deletion is an enforcement-class write
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {
            "input": f"*** Delete File: {repo['main'] / 'yamlgraph' / 'x.py'}\n"
        },
        "session_id": "s888",
        "cwd": str(repo["main"]),
    }
    _, out = run_hook(payload, guard_root=repo["main"])
    assert decision_of(out) == "deny"


def test_parse_error_with_enforcement_target_fails_closed(repo, tmp_path):
    ghost = tmp_path / "nowhere" / "yamlgraph" / "x.py"
    _, out = run_hook(edit_payload(ghost, tmp_path / "nowhere"))
    assert decision_of(out) == "deny"


def test_parse_error_without_enforcement_target_allowed(repo, tmp_path):
    ghost = tmp_path / "nowhere" / "docs" / "x.md"
    _, out = run_hook(edit_payload(ghost, tmp_path / "nowhere"))
    assert decision_of(out) == "approve"


# ── AC-06/AC-08: terminal write grammar ──────────────────────────────


def test_redirect_to_enforcement_path_on_main_denied(repo):
    _, out = run_hook(
        terminal_payload("echo x > yamlgraph/f.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_tee_to_enforcement_path_on_main_denied(repo):
    _, out = run_hook(
        terminal_payload("echo x | tee tests/f.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_sed_inplace_on_main_denied(repo):
    _, out = run_hook(
        terminal_payload("sed -i '' s/a/b/ yamlgraph/f.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_cp_onto_enforcement_path_on_main_denied(repo):
    _, out = run_hook(
        terminal_payload("cp /tmp/x.py yamlgraph/x.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_directory_copy_materializing_enforcement_path_denied(repo, tmp_path):
    # review PR#476 P2: cp -r /tmp/src/yamlgraph . materializes ./yamlgraph
    src = tmp_path / "src" / "yamlgraph"
    src.mkdir(parents=True)
    _, out = run_hook(
        terminal_payload(f"cp -r {src} .", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_denial_cure_is_placeholder_free_and_executable(repo):
    # review PR#476 P3: the cure must be copy-pasteable as written
    _, out = run_hook(
        edit_payload(repo["main"] / "yamlgraph" / "x.py", repo["main"]),
        guard_root=repo["main"],
    )
    reason = reason_of(out)
    assert "worktree.sh new" in reason
    assert "<nnn>" not in reason and "<path" not in reason
    assert "eval" in reason  # self-contained create-and-cd form


def test_apply_patch_move_to_enforcement_path_denied(repo):
    # review round 4 P1: real move header is '*** Move to: <path>'
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {
            "input": (
                f"*** Update File: {repo['main'] / 'docs' / 'foo.md'}\n"
                f"*** Move to: {repo['main'] / 'yamlgraph' / 'foo.py'}\n"
            )
        },
        "session_id": "s888",
        "cwd": str(repo["main"]),
    }
    _, out = run_hook(payload, guard_root=repo["main"])
    assert decision_of(out) == "deny"


def test_whitespace_variant_inline_writer_denied(repo):
    # review round 4 P2: extra spaces must not skip the analyzer
    _, out = run_hook(
        terminal_payload(
            "python3    -c \"open('yamlgraph/x.py','w').write('x')\"",
            repo["main"],
        ),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_time_prefixed_readonly_allowed(repo):
    _, out = run_hook(
        terminal_payload("time cat yamlgraph/f.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


def test_time_prefixed_write_denied(repo):
    _, out = run_hook(
        terminal_payload("time sh -c 'echo x > yamlgraph/f.py'", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_time_prefixed_cp_denied(repo):
    # review PR#476 round 2 P1: the time wrapper hid the writer token
    _, out = run_hook(
        terminal_payload("time cp /tmp/source.py yamlgraph/target.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"


def test_rm_safe_merged_confirmed_removes_squash_merged_tree(wt_repo):
    # review PR#476 round 2 P2: squash merges never make the branch tip an
    # ancestor of main — the confirmed mode trusts the caller's PR check
    subprocess.run(
        [str(WORKTREE_SH), "new", "t5"], cwd=wt_repo, capture_output=True, text=True
    )
    wt = wt_repo / "tmp/worktrees/feat/t5"
    (wt / "work.py").write_text("squashed upstream")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "work")
    # simulate the squash: main gets an equivalent commit, branch tip is no ancestor
    (wt_repo / "work.py").write_text("squashed upstream")
    _git(wt_repo, "add", "-A")
    _git(wt_repo, "commit", "-m", "squash: work (#1)")
    default = subprocess.run(
        [str(WORKTREE_SH), "rm-safe", "t5"], cwd=wt_repo, capture_output=True, text=True
    )
    assert default.returncode != 0  # unconfirmed still refused
    confirmed = subprocess.run(
        [str(WORKTREE_SH), "rm-safe", "t5", "--merged-confirmed"],
        cwd=wt_repo,
        capture_output=True,
        text=True,
    )
    assert confirmed.returncode == 0, confirmed.stderr
    assert not wt.exists()


def test_redirect_inside_worktree_allowed(repo):
    _, out = run_hook(
        terminal_payload("echo x > yamlgraph/f.py", repo["wt"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


# ── AC-07: escape hatch — narrow, audited, no cross-bypass ───────────


def test_escape_prefix_allows_and_audits(repo, tmp_path):
    log_dir = tmp_path / "logs"
    _, out = run_hook(
        terminal_payload(
            "FR888_ALLOW_MAIN=1 sh -c 'echo x > yamlgraph/f.py'", repo["main"]
        ),
        log_dir=log_dir,
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"
    rows = (log_dir / "audit.jsonl").read_text().splitlines()
    assert any("fr888-main-write-override" in r for r in rows)


def test_escape_does_not_bypass_authoring_guard(repo):
    _, out = run_hook(
        terminal_payload(
            "FR888_ALLOW_MAIN=1 sh -c 'echo x > examples/demos/hello/graph.yaml'",
            repo["main"],
        ),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"  # FR-767 still owns governed artifacts


# ── AC-05: worktree.sh contract — .env symlink + final cd line ───────


@pytest.fixture
def wt_repo(tmp_path):
    """Standalone fixture repo for worktree.sh (needs main branch + .env)."""
    main = tmp_path / "repo"
    main.mkdir()
    _git(main, "init", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    (main / "README.md").write_text("x")
    _git(main, "add", "-A")
    _git(main, "commit", "-m", "init")
    (main / ".env").write_text("KEY=1\n")
    (main / ".venv").mkdir()
    return main


def test_worktree_new_symlinks_env_and_prints_cd(wt_repo):
    r = subprocess.run(
        [str(WORKTREE_SH), "new", "t1"],
        cwd=wt_repo,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": os.environ["PATH"]},
    )
    assert r.returncode == 0, r.stderr
    wt = wt_repo / "tmp/worktrees/feat/t1"
    assert (wt / ".env").is_file() or (wt / ".env").is_symlink()
    last = r.stdout.strip().splitlines()[-1]
    assert last.startswith("cd ") and "feat/t1" in last


# ── AC-11: safe removal — untracked files block automatic prune ──────


def test_rm_safe_refuses_tree_with_untracked_files(wt_repo):
    subprocess.run(
        [str(WORKTREE_SH), "new", "t2"], cwd=wt_repo, capture_output=True, text=True
    )
    wt = wt_repo / "tmp/worktrees/feat/t2"
    (wt / "draft.md").write_text("unlanded work")
    r = subprocess.run(
        [str(WORKTREE_SH), "rm-safe", "t2"],
        cwd=wt_repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert wt.exists()  # never auto-removed with untracked files


def test_rm_safe_refuses_unmerged_committed_branch(wt_repo):
    # review PR#476 P1: committed-but-unmerged work must never be deleted
    subprocess.run(
        [str(WORKTREE_SH), "new", "t4"], cwd=wt_repo, capture_output=True, text=True
    )
    wt = wt_repo / "tmp/worktrees/feat/t4"
    (wt / "work.py").write_text("committed but unmerged")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "unmerged work")
    r = subprocess.run(
        [str(WORKTREE_SH), "rm-safe", "t4"],
        cwd=wt_repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert wt.exists()


def test_rm_safe_removes_clean_merged_tree(wt_repo):
    subprocess.run(
        [str(WORKTREE_SH), "new", "t3"], cwd=wt_repo, capture_output=True, text=True
    )
    wt = wt_repo / "tmp/worktrees/feat/t3"
    r = subprocess.run(
        [str(WORKTREE_SH), "rm-safe", "t3"],
        cwd=wt_repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert not wt.exists()
