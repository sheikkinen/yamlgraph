#!/usr/bin/env python3
"""Tests for .github/hooks/scripts/pre-command-guard.sh

Covers: Co-authored-by trailers, --no-verify blocker, multiline commit -m guard,
        audit logging (FR-414), fail-closed on parse error.

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


if __name__ == "__main__":
    sys.exit(main())
