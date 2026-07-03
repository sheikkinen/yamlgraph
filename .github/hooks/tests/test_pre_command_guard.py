#!/usr/bin/env python3
"""Tests for .github/hooks/scripts/pre-command-guard.sh

Covers: Co-authored-by trailers, --no-verify blocker, multiline commit -m guard,
        pipe-buffer guard (FR-440), audit logging (FR-414), fail-closed on parse error.

Run:  python3 .github/hooks/tests/test_pre_command_guard.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "pre-command-guard.sh"


def run_hook(
    payload, *, log_dir: str | None = None, raw_input: str | None = None
) -> tuple[int, str, list[dict]]:
    """Run hook, return (exit_code, stdout, audit_log_entries).

    If log_dir is provided, sets HOOK_LOG_DIR and reads audit.jsonl after.
    If raw_input is provided, sends it as-is instead of json.dumps(payload).
    """
    inp = raw_input if raw_input is not None else json.dumps(payload)
    env = {**os.environ}
    if log_dir:
        env["HOOK_LOG_DIR"] = log_dir
    r = subprocess.run(
        [str(HOOK)],
        input=inp,
        capture_output=True,
        text=True,
        env=env,
    )
    entries = []
    if log_dir:
        logfile = Path(log_dir) / "audit.jsonl"
        if logfile.exists():
            for line in logfile.read_text().strip().splitlines():
                if line.strip():
                    entries.append(json.loads(line))
    return r.returncode, r.stdout.strip(), entries


TESTS: list[tuple[str, dict, str]] = [
    # (name, JSON payload, expected: "approve" | "deny")
    # --- approve cases ---
    (
        "non-terminal tool",
        {"toolName": "read_file", "toolInput": {"path": "foo.py"}},
        "approve",
    ),
    (
        "clean git commit",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": 'git commit -m "fix: something"'},
        },
        "approve",
    ),
    (
        "grep co-authored-by (search)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "grep co-authored-by README.md"},
        },
        "approve",
    ),
    (
        "rg search for pattern",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "rg -n co-authored-by .github/"},
        },
        "approve",
    ),
    (
        "git commit -F (no trailer in cmd)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git commit -F ./tmp/msg.txt"},
        },
        "approve",
    ),
    (
        "send_to_terminal bare text (no commit context)",
        {
            "toolName": "send_to_terminal",
            "toolInput": {"command": "co-authored-by: Claude"},
        },
        "approve",
    ),
    # --- deny cases ---
    (
        "commit WITH Co-authored-by trailer",
        {
            "toolName": "run_in_terminal",
            "toolInput": {
                "command": 'git commit -m "fix: something\n\nCo-authored-by: Copilot <copilot@github.com>"',
            },
        },
        "deny",
    ),
    (
        "echo trailer to file",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": 'echo "Co-authored-by: Copilot" >> msg.txt'},
        },
        "deny",
    ),
    (
        "printf trailer to file",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": 'printf "Co-authored-by: Claude" > commit.msg'},
        },
        "deny",
    ),
    (
        "git merge with trailer",
        {
            "toolName": "run_in_terminal",
            "toolInput": {
                "command": 'git merge --no-ff -m "merge\n\nCo-authored-by: bot"',
            },
        },
        "deny",
    ),
    # --- --no-verify blocker ---
    (
        "git commit --no-verify blocked",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": 'git commit --no-verify -m "yolo"'},
        },
        "deny",
    ),
    (
        "git push --no-verify blocked",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git push --no-verify"},
        },
        "deny",
    ),
    (
        "pre-commit --no-verify blocked",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "pre-commit run --no-verify"},
        },
        "deny",
    ),
    (
        "grep --no-verify allowed (search)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "grep --no-verify README.md"},
        },
        "approve",
    ),
    (
        "--no-verify in echo/string context allowed",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": 'echo "--no-verify flag is forbidden"'},
        },
        "approve",
    ),
    # --- multiline commit -m guard ---
    (
        "multiline git commit -m blocked",
        {
            "toolName": "run_in_terminal",
            "toolInput": {
                "command": 'git commit -m "feat: something\n\nBody text here"'
            },
        },
        "deny",
    ),
    (
        "single-line git commit -m allowed",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": 'git commit -m "fix: one liner"'},
        },
        "approve",
    ),
    (
        "git commit -F allowed (correct pattern)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git commit -F ./tmp/msg.txt"},
        },
        "approve",
    ),
    (
        "git commit -m with literal backslash-n in body",
        {
            "toolName": "run_in_terminal",
            "toolInput": {
                "command": 'git commit -m "feat(scope): FR-100 title\n\ndetails"'
            },
        },
        "deny",
    ),
    # --- pipe-buffer guard (FR-440) ---
    (
        "pytest piped to tail denied",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "pytest tests/ -v 2>&1 | tail -20"},
        },
        "deny",
    ),
    (
        "pytest piped to head denied",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "pytest tests/ -q | head -5"},
        },
        "deny",
    ),
    (
        "pytest with tee then tail allowed",
        {
            "toolName": "run_in_terminal",
            "toolInput": {
                "command": "pytest tests/ -v 2>&1 | tee logs/run.log | tail -20"
            },
        },
        "approve",
    ),
    (
        "pytest without pipe allowed",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "pytest tests/ -v --no-cov"},
        },
        "approve",
    ),
    (
        "cat piped to tail allowed (not pytest)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "cat logs/run.log | tail -20"},
        },
        "approve",
    ),
    # --- branch creation guard (FR-662) ---
    (
        "git checkout -b denied",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git checkout -b feat/something"},
        },
        "deny",
    ),
    (
        "git switch -c denied",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git switch -c fix/branch-name"},
        },
        "deny",
    ),
    (
        "git branch <name> denied",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch feat/new-thing"},
        },
        "deny",
    ),
    (
        "git branch -d allowed (deletion)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch -d feat/old-thing"},
        },
        "approve",
    ),
    (
        "git branch -D allowed (force deletion)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch -D feat/old-thing"},
        },
        "approve",
    ),
    (
        "git branch -a allowed (listing)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch -a"},
        },
        "approve",
    ),
    (
        "git branch --merged allowed (query)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch --merged main"},
        },
        "approve",
    ),
    (
        "git branch --show-current allowed",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch --show-current"},
        },
        "approve",
    ),
    (
        "git checkout main allowed (switching)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git checkout main"},
        },
        "approve",
    ),
    (
        "git switch main allowed (switching)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git switch main"},
        },
        "approve",
    ),
    (
        "git branch -r allowed (remote listing)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch -r"},
        },
        "approve",
    ),
    (
        "git branch --contains allowed (query)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch --contains abc123"},
        },
        "approve",
    ),
    (
        "git branch --sort allowed (query)",
        {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git branch --sort=-committerdate"},
        },
        "approve",
    ),
]


def main() -> int:
    passed = 0
    failed = 0

    # ── Data-driven tests (existing) ──
    for name, payload, expected in TESTS:
        inp = json.dumps(payload)
        r = subprocess.run(
            [str(HOOK)],
            input=inp,
            capture_output=True,
            text=True,
        )
        output = r.stdout.strip()
        got = "deny" if "deny" in output else "approve"
        if got == expected:
            passed += 1
            print(f"  PASS: {name}")
        else:
            failed += 1
            print(f"  FAIL: {name} — expected {expected}, got {got}")
            print(f"         output: {output[:200]}")

    # ── Audit logging tests (FR-414) ──
    audit_tests = [
        test_malformed_json_denies,
        test_read_file_logs_pass_not_inspected,
        test_terminal_deny_logs_audit,
        test_terminal_approve_logs_audit,
        test_session_id_in_audit_entry,
        test_session_id_absent_when_not_in_payload,
        test_tool_use_id_in_audit_entry,
        test_lockdown_set,
        test_lockdown_blocks_subsequent_tools,
        test_lockdown_unlock,
        test_lockdown_status,
        test_lockdown_unknown_command,
        test_pipe_buffer_deny_logs_audit,
        test_branch_create_deny_logs_audit,
    ]
    for test in audit_tests:
        name = test.__name__
        try:
            test()
            passed += 1
            print(f"  PASS: {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL: {name} — {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR: {name} — {type(e).__name__}: {e}")

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


# ── Audit logging tests (FR-414) ──────────────────────────────────────


def test_malformed_json_denies():
    """Malformed JSON input must be denied (fail-closed), not approved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code, out, entries = run_hook(
            {}, raw_input="NOT VALID JSON {{{", log_dir=tmpdir
        )
        assert code == 0, f"exit {code}"
        assert "deny" in out, f"expected deny on malformed JSON, got: {out}"
        assert len(entries) >= 1, f"expected audit log entry, got {len(entries)}"
        assert (
            entries[-1]["decision"] == "deny"
        ), f"expected deny in audit, got: {entries[-1]}"
        assert (
            entries[-1]["reason"] == "parse-error"
        ), f"expected parse-error reason, got: {entries[-1]}"


def test_read_file_logs_pass_not_inspected():
    """Non-terminal tools must be logged as pass/not-inspected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {"toolName": "read_file", "toolInput": {"filePath": "/some/file.py"}}
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0, f"exit {code}"
        assert "deny" not in out, f"unexpected deny: {out}"
        assert len(entries) >= 1, f"expected audit log entry, got {len(entries)}"
        e = entries[-1]
        assert e["tool"] == "read_file", f"expected tool=read_file, got: {e}"
        assert e["decision"] == "pass", f"expected decision=pass, got: {e}"
        assert (
            e["reason"] == "not-inspected"
        ), f"expected reason=not-inspected, got: {e}"


def test_terminal_deny_logs_audit():
    """Denied commands must produce a deny audit entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "toolName": "run_in_terminal",
            "toolInput": {"command": 'git commit -m "feat\n\nCo-authored-by: bot"'},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert "deny" in out
        assert len(entries) >= 1, f"expected audit log entry, got {len(entries)}"
        e = entries[-1]
        assert e["decision"] == "deny", f"expected deny, got: {e}"
        assert (
            e["reason"] == "co-authored-by"
        ), f"expected co-authored-by reason, got: {e}"


def test_terminal_approve_logs_audit():
    """Approved terminal commands must produce an approve audit entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git add ."},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert "deny" not in out
        assert len(entries) >= 1, f"expected audit log entry, got {len(entries)}"
        e = entries[-1]
        assert e["decision"] == "approve", f"expected approve, got: {e}"
        assert "ts" in e, f"missing timestamp: {e}"
        assert e["hook"] == "pre-command-guard", f"wrong hook name: {e}"


# ── session_id tests ──────────────────────────────────────────────────


def test_session_id_in_audit_entry():
    """session_id from payload must appear in audit log entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "session_id": "abc-123-session",
            "tool_name": "read_file",
            "tool_input": {"filePath": "/some/file.py"},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert len(entries) >= 1
        e = entries[-1]
        assert (
            e.get("session_id") == "abc-123-session"
        ), f"expected session_id in audit entry, got: {e}"


def test_session_id_absent_when_not_in_payload():
    """When payload has no session_id, audit entry should omit or empty it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {"toolName": "read_file", "toolInput": {"filePath": "/f.py"}}
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert len(entries) >= 1
        e = entries[-1]
        assert e.get("session_id", "") == "", f"expected no session_id, got: {e}"


def test_tool_use_id_in_audit_entry():
    """tool_use_id from payload must appear in audit log entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "session_id": "sess-1",
            "tool_use_id": "toolu_vrtx_01ABC",
            "tool_name": "run_in_terminal",
            "tool_input": {"command": "echo hello"},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert len(entries) >= 1
        e = entries[-1]
        assert (
            e.get("tool_use_id") == "toolu_vrtx_01ABC"
        ), f"expected tool_use_id in audit entry, got: {e}"


# ── Lockdown command channel tests ───────────────────────────────────


def test_lockdown_set():
    """hookctl lockdown must create lockfile and deny with confirmation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "session_id": "sess-lockdown",
            "tool_name": "run_in_terminal",
            "tool_input": {"command": ".github/hooks/cmd lockdown"},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert "deny" in out, f"lockdown should deny (as response channel): {out}"
        # Lockfile must exist
        lockfile = Path(tmpdir) / ".lockdown"
        assert lockfile.exists(), "lockdown should create .lockdown file"
        # Audit entry must log the command
        assert len(entries) >= 1
        e = entries[-1]
        assert e["reason"] == "lockdown-set", f"wrong reason: {e}"


def test_lockdown_blocks_subsequent_tools():
    """When lockdown is active, ALL tool calls must be denied."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # First, activate lockdown
        lockdown_payload = {
            "session_id": "sess-lock",
            "tool_name": "run_in_terminal",
            "tool_input": {"command": ".github/hooks/cmd lockdown"},
        }
        run_hook(lockdown_payload, log_dir=tmpdir)

        # Now try a normal tool — should be denied
        normal_payload = {
            "session_id": "sess-lock",
            "tool_name": "read_file",
            "tool_input": {"filePath": "/foo.py"},
        }
        code, out, entries = run_hook(normal_payload, log_dir=tmpdir)
        assert "deny" in out, f"lockdown should block all tools: {out}"
        e = entries[-1]
        assert e["reason"] == "lockdown-active", f"wrong reason: {e}"


def test_lockdown_unlock():
    """hookctl unlock must remove lockfile and allow subsequent tools."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Activate lockdown
        run_hook(
            {
                "tool_name": "run_in_terminal",
                "tool_input": {"command": ".github/hooks/cmd lockdown"},
            },
            log_dir=tmpdir,
        )
        assert (Path(tmpdir) / ".lockdown").exists()

        # Unlock
        code, out, entries = run_hook(
            {
                "tool_name": "run_in_terminal",
                "tool_input": {"command": ".github/hooks/cmd unlock"},
            },
            log_dir=tmpdir,
        )
        assert "deny" in out  # response channel
        assert not (Path(tmpdir) / ".lockdown").exists(), "lockfile should be removed"

        # Normal tool should work again
        code2, out2, entries2 = run_hook(
            {"tool_name": "read_file", "tool_input": {"filePath": "/f.py"}},
            log_dir=tmpdir,
        )
        assert "deny" not in out2, f"unlock should allow tools: {out2}"


def test_lockdown_status():
    """hookctl status must return audit summary in deny reason."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate some audit entries first
        run_hook(
            {
                "tool_name": "read_file",
                "tool_input": {"filePath": "/f.py"},
            },
            log_dir=tmpdir,
        )
        run_hook(
            {
                "tool_name": "run_in_terminal",
                "tool_input": {"command": 'git commit --no-verify -m "x"'},
            },
            log_dir=tmpdir,
        )

        # Now request status
        code, out, entries = run_hook(
            {
                "tool_name": "run_in_terminal",
                "tool_input": {"command": ".github/hooks/cmd status"},
            },
            log_dir=tmpdir,
        )
        assert "deny" in out  # response via deny channel
        # The reason should contain summary info
        parsed = json.loads(out)
        reason = parsed.get("hookSpecificOutput", {}).get(
            "permissionDecisionReason", ""
        )
        assert (
            "entries" in reason.lower() or "total" in reason.lower()
        ), f"status should show summary: {reason}"


def test_lockdown_unknown_command():
    """Unknown hookctl commands must deny with help text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "tool_name": "run_in_terminal",
            "tool_input": {"command": ".github/hooks/cmd bogus"},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert "deny" in out
        assert len(entries) >= 1
        e = entries[-1]
        assert e["reason"] == "lockdown-unknown", f"wrong reason: {e}"


# ── Pipe-buffer guard tests (FR-440) ─────────────────────────────────


def test_pipe_buffer_deny_logs_audit():
    """pytest | tail must be denied with pipe-buffer reason in audit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "pytest tests/ -v 2>&1 | tail -20"},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert "deny" in out
        assert len(entries) >= 1
        e = entries[-1]
        assert e["decision"] == "deny", f"expected deny, got: {e}"
        assert e["reason"] == "pipe-buffer", f"expected pipe-buffer reason, got: {e}"


def test_branch_create_deny_logs_audit():
    """git checkout -b must be denied with branch-create reason in audit (FR-662)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "toolName": "run_in_terminal",
            "toolInput": {"command": "git checkout -b feat/agent-branch"},
        }
        code, out, entries = run_hook(payload, log_dir=tmpdir)
        assert code == 0
        assert "deny" in out
        assert len(entries) >= 1
        e = entries[-1]
        assert e["decision"] == "deny", f"expected deny, got: {e}"
        assert (
            e["reason"] == "branch-create"
        ), f"expected branch-create reason, got: {e}"


if __name__ == "__main__":
    sys.exit(main())
