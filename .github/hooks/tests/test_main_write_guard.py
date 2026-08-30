#!/usr/bin/env python3
"""Tests for the FR-889 OS-enforced main-write lock (supersedes the
FR-888 terminal write grammar — deleted, see the FR-888 post-mortem).

Covers: kernel-level write denial on locked main (AC-01); lock/unlock
idempotency, mode preservation, audit and state marker (AC-02); sync
relock on success and failure (AC-03); edit-tool denial via the
extracted lintable module with worktree allowance (AC-04); the R-2
lock-mutator fence with git/sudo escapes (AC-05); structural absence of
the deleted grammar (AC-06/AC-07); carve-outs (AC-09); board line
(AC-10); worktree.sh .env + final cd line and safe removal (FR-888
retained surfaces).

Infrastructure test scope (FR-436): outside REQ-YG marker coverage.

Run:  pytest .github/hooks/tests/test_main_write_guard.py -q --no-cov
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "pre-command-guard.sh"
WORKTREE_SH = Path(__file__).resolve().parents[3] / "scripts" / "worktree.sh"
GIT = shutil.which("git") or "/usr/bin/git"
pytestmark = pytest.mark.req("REQ-YG-631")


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
    for d in (
        "yamlgraph",
        "tests",
        "scripts",
        "capabilities",
        ".github/hooks",
        "docs",
        "feature-requests",
    ):
        (main / d).mkdir(parents=True)
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


# ── AC-01/AC-02/AC-03/AC-09: the OS lock (FR-889) ────────────────────


def wt_sh(cwd, *args):
    return subprocess.run(
        [str(WORKTREE_SH), *args], cwd=cwd, capture_output=True, text=True
    )


@pytest.fixture
def lock_repo(tmp_path):
    """Cloned main checkout with governed roots; unlocked again on exit."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-b", "main")
    _git(origin, "config", "user.email", "t@t")
    _git(origin, "config", "user.name", "t")
    for d in (
        "yamlgraph",
        "tests",
        "scripts",
        "capabilities",
        ".github/hooks/scripts",
        "docs",
    ):
        (origin / d).mkdir(parents=True)
        (origin / d / ".keep").write_text("")
    (origin / "scripts" / "tool.sh").write_text("#!/bin/sh\n")
    (origin / "scripts" / "tool.sh").chmod(0o755)
    (origin / "yamlgraph" / "x.py").write_text("x = 1\n")
    _git(origin, "add", "-A")
    _git(origin, "commit", "-m", "init")
    main = tmp_path / "mainclone"
    subprocess.run(
        [GIT, "clone", "-q", str(origin), str(main)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    yield main
    subprocess.run(["/bin/chmod", "-R", "u+w", str(tmp_path)], check=False)


def _is_locked(main):
    return not os.access(main / "yamlgraph", os.W_OK)


def test_lock_main_makes_terminal_write_fail_at_the_kernel(lock_repo):
    r = wt_sh(lock_repo, "lock-main")
    assert r.returncode == 0, r.stderr
    w = subprocess.run(
        ["/bin/sh", "-c", "echo x > yamlgraph/f.py"],
        cwd=lock_repo,
        capture_output=True,
        text=True,
    )
    assert w.returncode != 0
    assert "ermission denied" in w.stderr  # the kernel, zero hook lines
    assert not (lock_repo / "yamlgraph" / "f.py").exists()


def test_lock_covers_in_place_edit_of_existing_file(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    with pytest.raises(PermissionError):
        (lock_repo / "yamlgraph" / "x.py").write_text("clobber")


def test_lock_and_unlock_are_idempotent(lock_repo):
    for _ in range(2):
        assert wt_sh(lock_repo, "lock-main").returncode == 0
        assert _is_locked(lock_repo)
    for _ in range(2):
        assert wt_sh(lock_repo, "unlock-main").returncode == 0
        assert not _is_locked(lock_repo)


def test_lock_cycle_preserves_exec_and_group_bits(lock_repo):
    tool = lock_repo / "scripts" / "tool.sh"
    before = stat.S_IMODE(tool.stat().st_mode)
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    assert wt_sh(lock_repo, "unlock-main").returncode == 0
    assert stat.S_IMODE(tool.stat().st_mode) == before


def test_unlock_writes_audit_row_and_state_marker(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    marker = lock_repo / ".github/hooks/state/main-lock.json"
    assert json.loads(marker.read_text())["state"] == "locked"
    assert wt_sh(lock_repo, "unlock-main").returncode == 0
    assert json.loads(marker.read_text())["state"] == "unlocked"
    rows = (lock_repo / ".github/hooks/logs/audit.jsonl").read_text()
    assert "fr889-main-unlock" in rows


def test_carveouts_stay_writable_under_lock(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    with (lock_repo / ".github/hooks/logs/audit.jsonl").open("a") as fh:
        fh.write("{}\n")
    (lock_repo / ".github/hooks/state/probe.json").write_text("{}")
    with pytest.raises(PermissionError):
        (lock_repo / ".github/hooks/scripts/probe.sh").write_text("")
    (lock_repo / "docs" / "note.md").write_text("docs lane open")


def test_sync_pulls_and_relocks(lock_repo, tmp_path):
    origin = tmp_path / "origin"
    (origin / "docs" / "update.md").write_text("upstream\n")
    _git(origin, "add", "-A")
    _git(origin, "commit", "-m", "upstream")
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    r = wt_sh(lock_repo, "sync")
    assert r.returncode == 0, r.stderr
    assert (lock_repo / "docs" / "update.md").exists()
    assert _is_locked(lock_repo)


def test_sync_relocks_even_when_pull_fails(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    _git(lock_repo, "remote", "set-url", "origin", "/nonexistent/void")
    r = wt_sh(lock_repo, "sync")
    assert r.returncode != 0
    assert _is_locked(lock_repo)
    marker = lock_repo / ".github/hooks/state/main-lock.json"
    assert json.loads(marker.read_text())["state"] == "locked"


def test_worktree_new_functions_on_locked_main(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    r = wt_sh(lock_repo, "new", "lockedwt")
    assert r.returncode == 0, r.stderr
    wt = lock_repo / "tmp/worktrees/feat/lockedwt"
    (wt / "yamlgraph" / "new.py").write_text("writable = True\n")


# ── AC-05: lock-mutator fence — verbs only; git and sudo pass ────────


def test_chmod_on_governed_root_on_main_denied_with_unlock_cure(repo):
    _, out = run_hook(
        terminal_payload("chmod -R u+w yamlgraph", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "deny"
    assert "unlock-main" in reason_of(out)


@pytest.mark.parametrize(
    "cmd",
    [
        "chflags nouchg tests",
        "setfacl -m u::rwx scripts",
        "FOO=1 chmod u+w capabilities",
    ],
)
def test_other_lock_mutators_on_main_denied(repo, cmd):
    _, out = run_hook(terminal_payload(cmd, repo["main"]), guard_root=repo["main"])
    assert decision_of(out) == "deny"


def test_sudo_chmod_is_human_authorized_and_passes(repo):
    _, out = run_hook(
        terminal_payload("sudo chmod -R u+w yamlgraph", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


def test_git_is_never_fenced(repo):
    _, out = run_hook(
        terminal_payload("git checkout -- yamlgraph", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


def test_chmod_in_linked_worktree_allowed(repo):
    _, out = run_hook(
        terminal_payload("chmod -R u+w yamlgraph", repo["wt"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


def test_chmod_on_docs_lane_allowed(repo):
    _, out = run_hook(
        terminal_payload("chmod u+w docs", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


def test_mention_of_verb_without_invocation_allowed(repo):
    _, out = run_hook(
        terminal_payload("echo chmod yamlgraph", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


# ── AC-06/AC-07: the grammar is deleted, structurally ────────────────

MAIN_WRITE_PY = HOOK.parent / "checks" / "main_write.py"


def _check7_region() -> str:
    src = HOOK.read_text()
    start = src.index("Check 7: main-write")
    end = src.index("# Only inspect run_in_terminal")
    return src[start:end]


@pytest.mark.parametrize(
    "token",
    ["write_targets", "tee", "sed", "rsync", "truncate", "perl", "finditer"],
)
def test_no_write_grammar_token_survives_in_main_write_check(token):
    assert token not in _check7_region()


def test_main_write_check_dispatches_to_lintable_module():
    assert MAIN_WRITE_PY.is_file()
    assert "checks/main_write.py" in _check7_region()


def test_main_write_module_carries_no_write_grammar():
    src = MAIN_WRITE_PY.read_text()
    for token in ("write_targets", "tee", "rsync", "truncate", "perl"):
        assert token not in src


def test_guard_is_below_the_widened_size_gate():
    assert len(HOOK.read_text().splitlines()) <= 450


def test_heredoc_python_count_decreased():
    assert HOOK.read_text().count("<<'PYEOF'") <= 1  # only FR-767 remains


# ── AC-10: board line — read-only, never fixes ───────────────────────


def test_now_board_reports_unlocked_main_with_age(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "vscode"))
    import now  # noqa: PLC0415

    repo_dir = tmp_path / "r"
    state_dir = repo_dir / ".github" / "hooks" / "state"
    state_dir.mkdir(parents=True)
    marker = state_dir / "main-lock.json"
    marker.write_text(json.dumps({"state": "unlocked", "ts": "x", "by": "t"}))
    old = time.time() - 7200
    os.utime(marker, (old, old))
    lines = now.main_lock_lines(repo_dir)
    assert lines and "unlocked" in lines[0].lower()
    assert "lock-main" in lines[0]
    marker.write_text(json.dumps({"state": "locked", "ts": "x", "by": "t"}))
    assert now.main_lock_lines(repo_dir) == []


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


def test_time_prefixed_readonly_allowed(repo):
    _, out = run_hook(
        terminal_payload("time cat yamlgraph/f.py", repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


def test_readonly_grep_with_writer_tokens_in_pattern_allowed(repo):
    # the condemned grammar's witnessed false-positive class (2026-08-30):
    # a grep whose PATTERN mentions writer tokens is a read
    _, out = run_hook(
        terminal_payload('grep -n "foo" yamlgraph/x.py tests/y.py', repo["main"]),
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"


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


# ── AC-04 escape hatch — edit tools only, audited (terminal retired) ─


def test_edit_tool_escape_allows_and_audits(repo, tmp_path):
    log_dir = tmp_path / "logs"
    _, out = run_hook(
        edit_payload(repo["main"] / "yamlgraph" / "f.py", repo["main"]),
        env_extra={"FR888_ALLOW_MAIN": "1"},
        log_dir=log_dir,
        guard_root=repo["main"],
    )
    assert decision_of(out) == "approve"
    rows = (log_dir / "audit.jsonl").read_text().splitlines()
    override = [r for r in rows if "fr888-main-write-override" in r]
    assert override
    # review round 5 P2: audit row records the NORMALIZED target path
    assert str((repo["main"] / "yamlgraph" / "f.py").resolve()) in override[-1]


def test_rm_safe_refuses_gitignore_with_real_edits(wt_repo):
    # review round 5 P1: only the setup's own '.venv' append is tolerated
    subprocess.run(
        [str(WORKTREE_SH), "new", "t6"], cwd=wt_repo, capture_output=True, text=True
    )
    wt = wt_repo / "tmp/worktrees/feat/t6"
    (wt / ".gitignore").write_text(".venv\nmy-real-work-pattern/\n")
    r = subprocess.run(
        [str(WORKTREE_SH), "rm-safe", "t6"],
        cwd=wt_repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert wt.exists()


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
    assert last.startswith("cd '") and "feat/t1" in last  # quoted, executable


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
