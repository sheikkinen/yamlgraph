#!/usr/bin/env python3
"""FR-902 AC-03/AC-08: PreToolUse session-lane ownership guard.

Once a session lane record exists, write-shaped tool calls targeting this
repository outside the owning lane are denied with the lane path; writes
inside the lane and read-only commands stay allowed; the escape hatch
bypasses only the FR-902 denial class.

Run:  pytest .github/hooks/tests/test_fr902_lane_guard.py -q --no-cov
"""

import json
import os
import subprocess

import pytest
from fr902_fixtures import (
    GUARD,
    SID,
    SID2,
    lane_path,
    make_repo,
    read_audit,
    run_session_verb,
    write_lane_record,
)

pytestmark = pytest.mark.req("REQ-YG-629")


def run_guard(payload, *, log_dir, guard_root, env_extra=None):
    env = {**os.environ}
    for k in ("FR902_ALLOW_OUTSIDE", "FR888_ALLOW_MAIN"):
        env.pop(k, None)
    env["HOOK_LOG_DIR"] = str(log_dir)
    env["HOOK_GUARD_ROOT"] = str(guard_root)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(
        [str(GUARD)],
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


@pytest.fixture
def laned(tmp_path):
    """Main repo + session lane + lane record in the log dir."""
    main = make_repo(tmp_path)
    assert run_session_verb(main, SID).returncode == 0
    lane = lane_path(main).resolve()
    log_dir = tmp_path / "logs"
    write_lane_record(log_dir, SID, lane, f"session/{SID}")
    return {"main": main, "lane": lane, "log_dir": log_dir}


def edit_payload(file_path, cwd, sid=SID):
    return {
        "tool_name": "create_file",
        "tool_input": {"filePath": str(file_path)},
        "session_id": sid,
        "cwd": str(cwd),
    }


def terminal_payload(command, cwd, sid=SID):
    return {
        "tool_name": "run_in_terminal",
        "tool_input": {"command": command},
        "session_id": sid,
        "cwd": str(cwd),
    }


# ── AC-03: deny outside, allow inside, read-only untouched ───────────


def test_edit_outside_lane_denied_with_lane_path(laned):
    # changelog: open runtime lane, so the denial is FR-902's, not Check 7's
    _, out = run_guard(
        edit_payload(laned["main"] / "changelog" / "new.md", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "deny"
    assert str(laned["lane"]) in reason_of(out)


def test_edit_inside_lane_allowed(laned):
    _, out = run_guard(
        edit_payload(laned["lane"] / "docs" / "new.md", laned["lane"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "approve"


def test_edit_outside_repo_allowed(laned, tmp_path):
    _, out = run_guard(
        edit_payload(tmp_path / "elsewhere.txt", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "approve"


def test_terminal_write_outside_lane_denied(laned):
    _, out = run_guard(
        terminal_payload("echo x > docs/a.md", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "deny"
    assert str(laned["lane"]) in reason_of(out)


def test_terminal_readonly_allowed(laned):
    _, out = run_guard(
        terminal_payload("git status && git log --oneline -3", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "approve"


def test_foreign_lane_write_denied(laned):
    assert run_session_verb(laned["main"], SID2).returncode == 0
    foreign = lane_path(laned["main"], SID2).resolve()
    _, out = run_guard(
        edit_payload(foreign / "docs" / "steal.md", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "deny"


def test_session_without_record_not_denied(laned):
    _, out = run_guard(
        edit_payload(laned["main"] / "changelog" / "new.md", laned["main"], sid=SID2),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "approve"


# ── AC-03 escape hatch: audited, bypasses only the FR-902 class ──────


def test_escape_hatch_allows_and_audits(laned):
    _, out = run_guard(
        edit_payload(laned["main"] / "changelog" / "new.md", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
        env_extra={"FR902_ALLOW_OUTSIDE": "1"},
    )
    assert decision_of(out) == "approve"
    assert any(
        e.get("reason") == "fr902-lane-override" for e in read_audit(laned["log_dir"])
    )


def test_escape_hatch_does_not_bypass_no_verify(laned):
    _, out = run_guard(
        terminal_payload("git commit --no-verify -m x", laned["lane"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
        env_extra={"FR902_ALLOW_OUTSIDE": "1"},
    )
    assert decision_of(out) == "deny"


def test_escape_hatch_does_not_bypass_coauthored(laned):
    _, out = run_guard(
        terminal_payload(
            'git commit -m "x" -m "Co-authored-by: Copilot <x@y>"',
            laned["lane"],
        ),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
        env_extra={"FR902_ALLOW_OUTSIDE": "1"},
    )
    assert decision_of(out) == "deny"


# ── FR-889 §4c: cwd-proxy heuristics retired (payload cwd ≠ terminal cwd)


def test_git_commit_no_longer_denied_by_cwd_proxy(laned):
    # witnessed false-positive class: in-lane `git commit` denied because
    # the hook payload cwd is always the workspace root, never the
    # terminal's actual cwd (FR-925 enforce session, 4 escapes)
    _, out = run_guard(
        terminal_payload("git commit -m x", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "approve"


def test_interpreter_without_explicit_target_allowed(laned):
    _, out = run_guard(
        terminal_payload("python3 -c 'print(42)'", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "approve"


def test_escape_env_prefix_after_cd_recognized(laned):
    # witnessed 2026-08-30 (session 6feda07b): escape genuinely set but
    # denied by the position-0 regex; tokenizer must find it per-segment
    _, out = run_guard(
        terminal_payload(
            "cd /tmp && FR902_ALLOW_OUTSIDE=1 touch docs/x.md",
            laned["main"],
        ),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "approve"
    assert any(
        e.get("reason") == "fr902-lane-override" for e in read_audit(laned["log_dir"])
    )


def test_explicit_out_of_lane_write_still_denied(laned):
    # the retirement is heuristics-only: resolvable targets stay guarded
    _, out = run_guard(
        terminal_payload("touch docs/steal.md", laned["main"]),
        log_dir=laned["log_dir"],
        guard_root=laned["main"],
    )
    assert decision_of(out) == "deny"
