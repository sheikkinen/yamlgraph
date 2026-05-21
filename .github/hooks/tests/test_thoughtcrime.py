#!/usr/bin/env python3
"""Tests for FR-438 Thoughtcrime Hook.

Covers: PostToolUse transcript scan, sentinel arming/denial, session isolation,
        UUID validation, graceful degradation, one-shot semantics, audit logging.

Run:  python3 .github/hooks/tests/test_thoughtcrime.py
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
SCAN_SCRIPT = HOOKS_ROOT / "scripts" / "thoughtcrime-scan.sh"
GUARD_SCRIPT = HOOKS_ROOT / "scripts" / "pre-command-guard.sh"


# ── Helpers ───────────────────────────────────────────────────────────


def make_transcript_entry(
    msg_type: str,
    content: str = "",
    reasoning_text: str = "",
    timestamp: str = "2026-05-21T06:00:00+00:00",
) -> str:
    """Build a single transcript JSONL line."""
    entry = {
        "type": msg_type,
        "timestamp": timestamp,
        "data": {"content": content},
    }
    if msg_type == "assistant.message" and reasoning_text:
        entry["data"]["reasoningText"] = reasoning_text
    return json.dumps(entry)


def write_transcript(tmpdir: str, session_id: str, lines: list[str]) -> Path:
    """Write a synthetic transcript JSONL to a fake workspace storage layout."""
    # Mimic: ~/Library/.../workspaceStorage/<hash>/GitHub.copilot-chat/transcripts/<sid>.jsonl
    transcript_dir = (
        Path(tmpdir)
        / "workspaceStorage"
        / "fakehash"
        / "GitHub.copilot-chat"
        / "transcripts"
    )
    transcript_dir.mkdir(parents=True)
    transcript = transcript_dir / f"{session_id}.jsonl"
    transcript.write_text("\n".join(lines) + "\n")
    return transcript


def run_scan(
    session_id: str,
    *,
    log_dir: str,
    home_dir: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Run thoughtcrime-scan.sh, return (exit_code, stdout, stderr)."""
    payload = {
        "toolName": "read_file",
        "toolInput": {"filePath": "/some/file.py"},
        "session_id": session_id,
    }
    env = {**os.environ, "HOOK_LOG_DIR": log_dir}
    if home_dir:
        env["HOME"] = home_dir
    if extra_env:
        env.update(extra_env)
    r = subprocess.run(
        [str(SCAN_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def run_guard(
    payload: dict,
    *,
    log_dir: str,
) -> tuple[int, str, list[dict]]:
    """Run pre-command-guard.sh, return (exit_code, stdout, audit_entries)."""
    env = {**os.environ, "HOOK_LOG_DIR": log_dir}
    r = subprocess.run(
        [str(GUARD_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    entries = []
    logfile = Path(log_dir) / "audit.jsonl"
    if logfile.exists():
        for line in logfile.read_text().strip().splitlines():
            if line.strip():
                entries.append(json.loads(line))
    return r.returncode, r.stdout.strip(), entries


def read_sentinel(log_dir: str, session_id: str) -> dict | None:
    """Read and parse a thoughtcrime sentinel file, or None."""
    sentinel = Path(log_dir) / f".thoughtcrime-{session_id}"
    if not sentinel.exists():
        return None
    return json.loads(sentinel.read_text())


# ── PostToolUse scan tests ────────────────────────────────────────────


def test_scan_arms_sentinel_on_thoughtcrime():
    """Transcript with forbidden phrase in reasoningText must arm sentinel."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        os.makedirs(log_dir)
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        lines = [
            make_transcript_entry("user.message", content="fix the tests"),
            make_transcript_entry(
                "assistant.message",
                content="I'll look at the test suite.",
                reasoning_text="This is a pre-existing failure so I'll skip it.",
            ),
        ]
        home = str(Path(tmpdir))
        # Create workspace storage structure under fake HOME
        ws_dir = Path(home) / "Library" / "Application Support" / "Code" / "User"
        ws_dir.mkdir(parents=True)
        # Symlink our fake workspaceStorage into the expected path
        storage_src = Path(tmpdir) / "workspaceStorage"
        storage_src.mkdir()
        (ws_dir / "workspaceStorage").symlink_to(storage_src)
        # Write transcript
        t_dir = storage_src / "fakehash" / "GitHub.copilot-chat" / "transcripts"
        t_dir.mkdir(parents=True)
        (t_dir / f"{sid}.jsonl").write_text("\n".join(lines) + "\n")

        code, stdout, stderr = run_scan(sid, log_dir=log_dir, home_dir=home)
        assert code == 0, f"exit {code}, stderr: {stderr}"
        sentinel = read_sentinel(log_dir, sid)
        assert sentinel is not None, "sentinel must be armed on thoughtcrime"
        assert "pre-existing failure" in sentinel.get("phrase", "").lower()
        assert sentinel.get("doctrine", "") != ""


def test_scan_no_sentinel_on_clean_thinking():
    """Transcript without forbidden phrases must NOT arm sentinel."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        os.makedirs(log_dir)
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        lines = [
            make_transcript_entry("user.message", content="fix the tests"),
            make_transcript_entry(
                "assistant.message",
                content="I'll investigate the test failures.",
                reasoning_text="Let me examine the test suite and fix any issues.",
            ),
        ]
        home = str(Path(tmpdir))
        ws_dir = Path(home) / "Library" / "Application Support" / "Code" / "User"
        ws_dir.mkdir(parents=True)
        storage_src = Path(tmpdir) / "workspaceStorage"
        storage_src.mkdir()
        (ws_dir / "workspaceStorage").symlink_to(storage_src)
        t_dir = storage_src / "fakehash" / "GitHub.copilot-chat" / "transcripts"
        t_dir.mkdir(parents=True)
        (t_dir / f"{sid}.jsonl").write_text("\n".join(lines) + "\n")

        code, stdout, stderr = run_scan(sid, log_dir=log_dir, home_dir=home)
        assert code == 0, f"exit {code}, stderr: {stderr}"
        sentinel = read_sentinel(log_dir, sid)
        assert sentinel is None, "sentinel must NOT be armed on clean thinking"


def test_scan_only_latest_message():
    """Only the LATEST assistant.message should be scanned, not earlier ones."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        os.makedirs(log_dir)
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        lines = [
            # Earlier message has thoughtcrime
            make_transcript_entry(
                "assistant.message",
                content="Earlier response",
                reasoning_text="This is a pre-existing failure, skip it.",
                timestamp="2026-05-21T05:00:00+00:00",
            ),
            make_transcript_entry("user.message", content="try again"),
            # Latest message is clean
            make_transcript_entry(
                "assistant.message",
                content="I'll own this and fix it properly.",
                reasoning_text="Let me take ownership and fix the root cause.",
                timestamp="2026-05-21T06:00:00+00:00",
            ),
        ]
        home = str(Path(tmpdir))
        ws_dir = Path(home) / "Library" / "Application Support" / "Code" / "User"
        ws_dir.mkdir(parents=True)
        storage_src = Path(tmpdir) / "workspaceStorage"
        storage_src.mkdir()
        (ws_dir / "workspaceStorage").symlink_to(storage_src)
        t_dir = storage_src / "fakehash" / "GitHub.copilot-chat" / "transcripts"
        t_dir.mkdir(parents=True)
        (t_dir / f"{sid}.jsonl").write_text("\n".join(lines) + "\n")

        code, stdout, stderr = run_scan(sid, log_dir=log_dir, home_dir=home)
        assert code == 0
        sentinel = read_sentinel(log_dir, sid)
        assert (
            sentinel is None
        ), "earlier thoughtcrime should NOT trigger on latest-only scan"


def test_scan_detects_variant_phrases():
    """Variants like 'preexisting failure' and 'was already broken' must match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        os.makedirs(log_dir)
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        lines = [
            make_transcript_entry(
                "assistant.message",
                content="Looking at the tests.",
                reasoning_text="This was already broken before my changes.",
            ),
        ]
        home = str(Path(tmpdir))
        ws_dir = Path(home) / "Library" / "Application Support" / "Code" / "User"
        ws_dir.mkdir(parents=True)
        storage_src = Path(tmpdir) / "workspaceStorage"
        storage_src.mkdir()
        (ws_dir / "workspaceStorage").symlink_to(storage_src)
        t_dir = storage_src / "fakehash" / "GitHub.copilot-chat" / "transcripts"
        t_dir.mkdir(parents=True)
        (t_dir / f"{sid}.jsonl").write_text("\n".join(lines) + "\n")

        code, stdout, stderr = run_scan(sid, log_dir=log_dir, home_dir=home)
        assert code == 0
        sentinel = read_sentinel(log_dir, sid)
        assert (
            sentinel is not None
        ), "variant 'was already broken' must trigger sentinel"


def test_scan_graceful_no_transcript():
    """When transcript file is absent, hook must exit 0 without arming."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        os.makedirs(log_dir)
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        home = str(Path(tmpdir))
        # Create workspace storage but NO transcript file
        ws_dir = Path(home) / "Library" / "Application Support" / "Code" / "User"
        ws_dir.mkdir(parents=True)
        storage_src = Path(tmpdir) / "workspaceStorage"
        storage_src.mkdir()
        (ws_dir / "workspaceStorage").symlink_to(storage_src)

        code, stdout, stderr = run_scan(sid, log_dir=log_dir, home_dir=home)
        assert code == 0, f"must exit 0 on missing transcript, got {code}"
        sentinel = read_sentinel(log_dir, sid)
        assert sentinel is None


def test_scan_graceful_no_reasoning_text():
    """When reasoningText is absent, hook must exit 0 without arming."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        os.makedirs(log_dir)
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        lines = [
            make_transcript_entry(
                "assistant.message",
                content="This is a pre-existing failure in the test suite.",
                reasoning_text="",  # no reasoning text
            ),
        ]
        home = str(Path(tmpdir))
        ws_dir = Path(home) / "Library" / "Application Support" / "Code" / "User"
        ws_dir.mkdir(parents=True)
        storage_src = Path(tmpdir) / "workspaceStorage"
        storage_src.mkdir()
        (ws_dir / "workspaceStorage").symlink_to(storage_src)
        t_dir = storage_src / "fakehash" / "GitHub.copilot-chat" / "transcripts"
        t_dir.mkdir(parents=True)
        (t_dir / f"{sid}.jsonl").write_text("\n".join(lines) + "\n")

        code, stdout, stderr = run_scan(sid, log_dir=log_dir, home_dir=home)
        assert code == 0
        sentinel = read_sentinel(log_dir, sid)
        assert sentinel is None, "no reasoningText → no scan → no sentinel"


def test_scan_rejects_invalid_session_id():
    """Non-UUID session_id must be rejected (path traversal guard)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        os.makedirs(log_dir)
        bad_ids = [
            "../../../etc/passwd",
            "not-a-uuid",
            "",
            "aaaaaaaa-bbbb-1ccc-9ddd",  # truncated
        ]
        for bad_id in bad_ids:
            code, stdout, stderr = run_scan(bad_id, log_dir=log_dir, home_dir=tmpdir)
            assert code == 0, f"must exit 0 on invalid session_id '{bad_id}'"
            sentinel_glob = list(Path(log_dir).glob(".thoughtcrime-*"))
            assert (
                len(sentinel_glob) == 0
            ), f"invalid session_id '{bad_id}' must not create sentinel"


# ── PreToolUse sentinel check tests ──────────────────────────────────


def test_guard_denies_on_armed_sentinel():
    """Pre-command-guard must deny when thoughtcrime sentinel exists for session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        sentinel = Path(tmpdir) / f".thoughtcrime-{sid}"
        sentinel.write_text(
            json.dumps(
                {
                    "phrase": "pre-existing failure",
                    "doctrine": "A red test suite belongs to the current change author.",
                    "scripture_ref": "copilot-instructions.md § Conventions",
                    "ts": "2026-05-21T06:00:00+00:00",
                }
            )
        )

        payload = {
            "session_id": sid,
            "toolName": "read_file",
            "toolInput": {"filePath": "/some/file.py"},
        }
        code, out, entries = run_guard(payload, log_dir=tmpdir)
        assert code == 0
        assert "deny" in out, f"sentinel must trigger deny, got: {out}"
        assert (
            "THOUGHTCRIME" in out.upper() or "thoughtcrime" in out.lower()
        ), f"deny message should mention thoughtcrime: {out}"
        # Sentinel must be deleted (one-shot)
        assert not sentinel.exists(), "sentinel must be deleted after denial (one-shot)"


def test_guard_approves_without_sentinel():
    """Pre-command-guard must approve when no sentinel exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        # No sentinel file created
        payload = {
            "session_id": sid,
            "toolName": "read_file",
            "toolInput": {"filePath": "/some/file.py"},
        }
        code, out, entries = run_guard(payload, log_dir=tmpdir)
        assert code == 0
        assert (
            "deny" not in out or "thoughtcrime" not in out.lower()
        ), f"no sentinel → no thoughtcrime deny: {out}"


def test_guard_session_isolation():
    """Sentinel for session A must NOT trigger denial for session B."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sid_a = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        sid_b = "bbbbbbbb-cccc-1ddd-9eee-ffffffffffff"
        sentinel = Path(tmpdir) / f".thoughtcrime-{sid_a}"
        sentinel.write_text(
            json.dumps(
                {
                    "phrase": "pre-existing failure",
                    "doctrine": "Own the red suite.",
                    "ts": "2026-05-21T06:00:00+00:00",
                }
            )
        )

        # Session B should NOT be denied
        payload_b = {
            "session_id": sid_b,
            "toolName": "read_file",
            "toolInput": {"filePath": "/some/file.py"},
        }
        code, out, entries = run_guard(payload_b, log_dir=tmpdir)
        assert (
            "thoughtcrime" not in out.lower()
        ), f"session B must not be affected by session A's sentinel: {out}"
        # Session A's sentinel must still exist (not consumed by B)
        assert sentinel.exists(), "session A's sentinel must survive session B's check"


def test_guard_one_shot_semantics():
    """After denial, the NEXT tool call from the same session must proceed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        sentinel = Path(tmpdir) / f".thoughtcrime-{sid}"
        sentinel.write_text(
            json.dumps(
                {
                    "phrase": "not introduced by this change",
                    "doctrine": "Assume ownership.",
                    "ts": "2026-05-21T06:00:00+00:00",
                }
            )
        )

        payload = {
            "session_id": sid,
            "toolName": "read_file",
            "toolInput": {"filePath": "/some/file.py"},
        }
        # First call: denied
        code1, out1, _ = run_guard(payload, log_dir=tmpdir)
        assert "deny" in out1

        # Second call: must proceed (sentinel consumed)
        code2, out2, _ = run_guard(payload, log_dir=tmpdir)
        assert (
            "thoughtcrime" not in out2.lower()
        ), f"second call must not be denied (one-shot): {out2}"


def test_guard_audit_on_thoughtcrime_deny():
    """Thoughtcrime denial must produce audit log entry with reason."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sid = "aaaaaaaa-bbbb-1ccc-9ddd-eeeeeeeeeeee"
        sentinel = Path(tmpdir) / f".thoughtcrime-{sid}"
        sentinel.write_text(
            json.dumps(
                {
                    "phrase": "pre-existing failure",
                    "doctrine": "Own it.",
                    "ts": "2026-05-21T06:00:00+00:00",
                }
            )
        )

        payload = {
            "session_id": sid,
            "toolName": "run_in_terminal",
            "toolInput": {"command": "echo hello"},
        }
        code, out, entries = run_guard(payload, log_dir=tmpdir)
        assert code == 0
        assert "deny" in out
        # Find the thoughtcrime audit entry
        tc_entries = [e for e in entries if e.get("reason") == "thoughtcrime"]
        assert (
            len(tc_entries) >= 1
        ), f"expected thoughtcrime audit entry, got: {entries}"
        assert tc_entries[-1]["decision"] == "deny"


# ── Runner ────────────────────────────────────────────────────────────


def main() -> int:
    tests = [
        # PostToolUse scan
        test_scan_arms_sentinel_on_thoughtcrime,
        test_scan_no_sentinel_on_clean_thinking,
        test_scan_only_latest_message,
        test_scan_detects_variant_phrases,
        test_scan_graceful_no_transcript,
        test_scan_graceful_no_reasoning_text,
        test_scan_rejects_invalid_session_id,
        # PreToolUse guard
        test_guard_denies_on_armed_sentinel,
        test_guard_approves_without_sentinel,
        test_guard_session_isolation,
        test_guard_one_shot_semantics,
        test_guard_audit_on_thoughtcrime_deny,
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
    raise SystemExit(main())
