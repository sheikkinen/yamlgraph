#!/usr/bin/env python3
"""Tests for .github/hooks/scripts/session-timeline.py

Covers: audit+transcript join, timestamp normalization, --filter, --json,
        graceful degradation without transcript, --session selection.

Run:  python3 .github/hooks/tests/test_session_timeline.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "session-timeline.py"


def run_timeline(
    *,
    audit_entries: list[dict],
    transcript_entries: list[dict] | None = None,
    args: list[str] | None = None,
) -> tuple[int, str]:
    """Create temp files, run script, return (exit_code, stdout)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_path = Path(tmpdir) / "audit.jsonl"
        audit_path.write_text("\n".join(json.dumps(e) for e in audit_entries) + "\n", encoding="utf-8")

        cmd = [sys.executable, str(SCRIPT), "--audit", str(audit_path)]

        if transcript_entries is not None:
            transcript_path = Path(tmpdir) / "transcript.jsonl"
            transcript_path.write_text(
                "\n".join(json.dumps(e) for e in transcript_entries) + "\n"
            , encoding="utf-8")
            cmd.extend(["--transcript", str(transcript_path)])

        if args:
            cmd.extend(args)

        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.returncode, r.stdout


# ── Test data ────────────────────────────────────────────────────────

AUDIT = [
    {
        "ts": "2026-05-20T06:26:56.000000+00:00",
        "hook": "pre-command-guard",
        "tool": "read_file",
        "decision": "pass",
        "reason": "not-inspected",
        "detail": '{"filePath": "/foo.py"}',
        "session_id": "sess-1",
    },
    {
        "ts": "2026-05-20T06:26:57.000000+00:00",
        "hook": "pre-command-guard",
        "tool": "run_in_terminal",
        "decision": "approve",
        "reason": "clean",
        "detail": "git status",
        "session_id": "sess-1",
    },
    {
        "ts": "2026-05-20T06:27:01.000000+00:00",
        "hook": "pre-command-guard",
        "tool": "run_in_terminal",
        "decision": "deny",
        "reason": "co-authored-by",
        "detail": 'git commit -m "Co-authored-by: bot"',
        "session_id": "sess-1",
    },
    {
        "ts": "2026-05-20T06:31:24.000000+00:00",
        "hook": "pre-command-guard",
        "tool": "create_file",
        "decision": "pass",
        "reason": "not-inspected",
        "detail": "{}",
        "session_id": "sess-1",
    },
]

# Transcript uses JS-style Z timestamps
TRANSCRIPT = [
    {
        "type": "session.start",
        "data": {},
        "id": "start-1",
        "timestamp": "2026-05-20T06:26:50.000Z",
    },
    {
        "type": "user.message",
        "data": {"content": "test the check-coauthor hook"},
        "id": "msg-1",
        "timestamp": "2026-05-20T06:26:55.000Z",
    },
    {
        "type": "user.message",
        "data": {"content": "create the config and save tests"},
        "id": "msg-2",
        "timestamp": "2026-05-20T06:31:23.000Z",
    },
]


# ── Tests ────────────────────────────────────────────────────────────


def test_basic_join():
    """Audit entries are grouped under the correct user message."""
    code, out = run_timeline(audit_entries=AUDIT, transcript_entries=TRANSCRIPT)
    assert code == 0, f"exit {code}: {out}"
    # First user message should appear before its tool calls
    assert "test the check-coauthor hook" in out
    assert "create the config" in out
    # Deny should be highlighted
    assert "DENY" in out or "deny" in out.lower()


def test_timestamp_normalization():
    """Python +00:00 and JS Z timestamps are correctly compared."""
    code, out = run_timeline(audit_entries=AUDIT, transcript_entries=TRANSCRIPT)
    assert code == 0, f"exit {code}: {out}"
    # The deny at 06:27:01 should be under "test the check-coauthor hook" (06:26:55)
    # not under "create the config" (06:31:23)
    lines = out.splitlines()
    coauthor_idx = next(
        (i for i, line in enumerate(lines) if "test the check-coauthor" in line), -1
    )
    create_idx = next(
        (i for i, line in enumerate(lines) if "create the config" in line), -1
    )
    deny_idx = next(
        (
            i
            for i, line in enumerate(lines)
            if "deny" in line.lower() and "co-authored" in line.lower()
        ),
        -1,
    )
    assert coauthor_idx >= 0, "missing coauthor user message in output"
    assert create_idx >= 0, "missing create user message in output"
    assert deny_idx >= 0, "missing deny line in output"
    assert (
        coauthor_idx < deny_idx < create_idx
    ), f"deny should be between coauthor({coauthor_idx}) and create({create_idx}), got {deny_idx}"


def test_filter_deny():
    """--filter deny shows only denied entries."""
    code, out = run_timeline(
        audit_entries=AUDIT, transcript_entries=TRANSCRIPT, args=["--filter", "deny"]
    )
    assert code == 0, f"exit {code}: {out}"
    assert "co-authored" in out.lower()
    # approve and pass entries should not appear as tool lines
    # (user message headers may still appear for context)
    lines = [line for line in out.splitlines() if line.strip().startswith("[")]
    tool_lines = [line for line in lines if "read_file" in line or "git status" in line]
    assert len(tool_lines) == 0, f"filter deny should hide approved tools: {tool_lines}"


def test_json_output():
    """--json produces valid JSON array."""
    code, out = run_timeline(
        audit_entries=AUDIT, transcript_entries=TRANSCRIPT, args=["--json"]
    )
    assert code == 0, f"exit {code}: {out}"
    data = json.loads(out)
    assert isinstance(data, list), f"expected list, got {type(data)}"
    assert len(data) > 0
    # Each entry should have trigger and decision
    for entry in data:
        assert "tool" in entry, f"missing tool: {entry}"
        assert "decision" in entry, f"missing decision: {entry}"


def test_audit_only_no_transcript():
    """Without transcript, shows audit entries without user prompt grouping."""
    code, out = run_timeline(audit_entries=AUDIT)
    assert code == 0, f"exit {code}: {out}"
    assert "read_file" in out
    assert "deny" in out.lower()


def test_session_filter():
    """--session filters audit entries by session_id."""
    mixed_audit = AUDIT + [
        {
            "ts": "2026-05-20T07:00:00.000000+00:00",
            "hook": "pre-command-guard",
            "tool": "grep_search",
            "decision": "pass",
            "reason": "not-inspected",
            "detail": "{}",
            "session_id": "sess-OTHER",
        },
    ]
    code, out = run_timeline(
        audit_entries=mixed_audit,
        transcript_entries=TRANSCRIPT,
        args=["--session", "sess-1"],
    )
    assert code == 0, f"exit {code}: {out}"
    assert "grep_search" not in out, "session filter should exclude sess-OTHER entries"
    assert "read_file" in out


def test_empty_audit():
    """Empty audit.jsonl produces no errors."""
    code, out = run_timeline(audit_entries=[], transcript_entries=TRANSCRIPT)
    assert code == 0, f"exit {code}: {out}"


def test_summary_line():
    """Output includes a summary with total counts."""
    code, out = run_timeline(audit_entries=AUDIT, transcript_entries=TRANSCRIPT)
    assert code == 0, f"exit {code}: {out}"
    lower = out.lower()
    assert "deny" in lower and (
        "1" in out or "total" in lower
    ), "summary should mention deny count"


def main() -> int:
    tests = [
        test_basic_join,
        test_timestamp_normalization,
        test_filter_deny,
        test_json_output,
        test_audit_only_no_transcript,
        test_session_filter,
        test_empty_audit,
        test_summary_line,
    ]
    passed = 0
    failed = 0
    for test in tests:
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


if __name__ == "__main__":
    sys.exit(main())
