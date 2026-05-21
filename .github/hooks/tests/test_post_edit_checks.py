#!/usr/bin/env python3
"""Tests for .github/hooks/scripts/post-edit-checks.sh

Run:  python3 .github/hooks/tests/test_post_edit_checks.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "post-edit-checks.sh"


def run_hook(payload: dict, *, log_dir: str | None = None) -> tuple[int, str]:
    """Run the hook script with JSON payload, return (exit_code, stdout)."""
    inp = json.dumps(payload)
    env = {**os.environ, "PATH": f".venv/bin:{os.environ.get('PATH', '')}"}
    if log_dir:
        env["HOOK_LOG_DIR"] = log_dir
    r = subprocess.run(
        [str(HOOK)],
        input=inp,
        capture_output=True,
        text=True,
        env=env,
    )
    return r.returncode, r.stdout.strip()


def read_audit_log(log_dir: str) -> list[dict]:
    """Read audit.jsonl entries from log_dir."""
    logfile = Path(log_dir) / "audit.jsonl"
    if not logfile.exists():
        return []
    entries = []
    for line in logfile.read_text().strip().splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def make_payload(tool_name: str, file_path: str) -> dict:
    """Build a PostToolUse JSON payload for a file-edit tool."""
    if tool_name == "multi_replace_string_in_file":
        return {
            "toolName": tool_name,
            "toolInput": {"replacements": [{"filePath": file_path}]},
        }
    return {"toolName": tool_name, "toolInput": {"filePath": file_path}}


# ── Skip non-file-edit tools ──────────────────────────────────────────


def test_skips_non_edit_tools():
    """Non-file-edit tools should be approved silently."""
    code, out = run_hook({"toolName": "read_file", "toolInput": {"filePath": "foo.py"}})
    assert code == 0, f"exit {code}"
    assert "systemMessage" not in out, f"unexpected systemMessage: {out}"


def test_skips_non_python_files():
    """Edits to non-target YAML files should be approved silently."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write("name: ci\non: push\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            assert "systemMessage" not in out, f"unexpected: {out}"
        finally:
            os.unlink(f.name)


def test_graph_yaml_invalid_reports_lint_errors():
    """Graph YAML with nodes/edges and invalid content should be linted and flagged."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write(
            "nodes:\n"
            "  bad:\n"
            "    type: does_not_exist\n"
            "edges:\n"
            "  - from: START\n"
            "    to: bad\n"
            "  - from: bad\n"
            "    to: END\n"
        )
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "graph lint issues" in msg.lower(), f"expected graph lint: {msg}"
        finally:
            os.unlink(f.name)


def test_graph_yaml_valid_no_message():
    """A known-valid graph YAML should pass with no systemMessage."""
    repo_root = Path(__file__).resolve().parents[3]
    graph_path = repo_root / "examples" / "demos" / "hello" / "graph.yaml"
    code, out = run_hook(make_payload("replace_string_in_file", str(graph_path)))
    assert code == 0
    if out:
        parsed = json.loads(out)
        msg = parsed.get("systemMessage", "")
        assert msg == "", f"unexpected issues for valid graph: {msg}"


def test_prompt_yaml_parse_error_reported():
    """Invalid YAML under prompts/ should emit prompt parse errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_dir = Path(tmpdir) / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / "bad.yaml"
        prompt_file.write_text("template: [broken\n", encoding="utf-8")

        code, out = run_hook(make_payload("replace_string_in_file", str(prompt_file)))
        assert code == 0
        parsed = json.loads(out)
        msg = parsed.get("systemMessage", "")
        assert "prompt file error" in msg.lower(), f"expected prompt parse error: {msg}"


def test_prompt_yaml_valid_no_message():
    """Valid YAML under prompts/ should pass parse check with no message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_dir = Path(tmpdir) / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / "ok.yaml"
        prompt_file.write_text("template: hello\n", encoding="utf-8")

        code, out = run_hook(make_payload("replace_string_in_file", str(prompt_file)))
        assert code == 0
        if out:
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert msg == "", f"unexpected prompt issues: {msg}"


# ── Ruff lint ─────────────────────────────────────────────────────────


def test_ruff_lint_catches_errors():
    """Ruff lint errors should appear in systemMessage."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import os\nimport sys\n\nx = 1\n")  # unused imports
        f.flush()
        try:
            code, out = run_hook(make_payload("create_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "ruff" in msg.lower() or "F401" in msg
            ), f"expected ruff lint error: {msg}"
        finally:
            os.unlink(f.name)


def test_ruff_format_catches_issues():
    """Ruff format issues should appear in systemMessage."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x=1;y=2;z=3\n")  # poor formatting
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "format" in msg.lower() or "ruff" in msg.lower()
            ), f"expected format issue: {msg}"
        finally:
            os.unlink(f.name)


# ── Forbidden terms ──────────────────────────────────────────────────


def test_forbid_terms_catches_todo():
    """TODO in Python source should be flagged."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1  # TODO: fix this\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "TODO" in msg or "forbidden" in msg.lower()
            ), f"expected TODO warning: {msg}"
        finally:
            os.unlink(f.name)


def test_forbid_terms_catches_fixme():
    """FIXME in Python source should be flagged."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1  # FIXME: broken\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "FIXME" in msg or "forbidden" in msg.lower()
            ), f"expected FIXME warning: {msg}"
        finally:
            os.unlink(f.name)


def test_forbid_terms_catches_backward_compat():
    """'backward compatibility' in Python source should be flagged."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("# keeping for backward compatibility\nx = 1\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "backward" in msg.lower() or "forbidden" in msg.lower()
            ), f"expected warning: {msg}"
        finally:
            os.unlink(f.name)


# ── File size ────────────────────────────────────────────────────────


def test_file_size_warns_over_400():
    """Files over 400 lines should produce a warning."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\n" * 410)
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "410" in msg or "lines" in msg.lower()
            ), f"expected size warning: {msg}"
        finally:
            os.unlink(f.name)


def test_file_size_errors_over_450():
    """Files over 450 lines should produce an error."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\n" * 460)
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "460" in msg or "450" in msg, f"expected size error: {msg}"
        finally:
            os.unlink(f.name)


# ── Debug statements ─────────────────────────────────────────────────


def test_debug_breakpoint():
    """breakpoint() calls should be flagged."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\nbreakpoint()\ny = 2\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "breakpoint" in msg or "debug" in msg.lower()
            ), f"expected debug warning: {msg}"
        finally:
            os.unlink(f.name)


def test_debug_pdb_import():
    """import pdb should be flagged."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pdb\npdb.set_trace()\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "pdb" in msg or "debug" in msg.lower()
            ), f"expected pdb warning: {msg}"
        finally:
            os.unlink(f.name)


# ── Clean file ───────────────────────────────────────────────────────


def test_clean_file_no_message():
    """A clean Python file should produce no systemMessage."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\ny = 2\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            # Should either be empty or have no systemMessage
            if out:
                parsed = json.loads(out)
                msg = parsed.get("systemMessage", "")
                assert msg == "", f"unexpected issues on clean file: {msg}"
        finally:
            os.unlink(f.name)


# ── multi_replace_string_in_file ──────────────────────────────────────


def test_multi_replace_extracts_filepath():
    """multi_replace_string_in_file has filePath inside replacements array."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1  # TODO: remove\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("multi_replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "TODO" in msg or "forbidden" in msg.lower(), f"expected TODO: {msg}"
        finally:
            os.unlink(f.name)


# ── noqa confession cross-reference ──────────────────────────────────


def test_noqa_undocumented_flagged():
    """A # noqa in a file not in confessions.md should be flagged."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import os  # noqa: F401\nx = 1\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "noqa" in msg.lower() or "confession" in msg.lower()
            ), f"expected noqa/confession warning: {msg}"
            assert "F401" in msg, f"expected error code F401 in message: {msg}"
        finally:
            os.unlink(f.name)


def test_noqa_blanket_flagged():
    """A blanket # noqa (no code) should be flagged."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import os  # noqa\nx = 1\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert (
                "noqa" in msg.lower() or "confession" in msg.lower()
            ), f"expected noqa warning: {msg}"
        finally:
            os.unlink(f.name)


def test_no_noqa_no_warning():
    """A file without # noqa should produce no confession warning."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\ny = 2\n")
        f.flush()
        try:
            code, out = run_hook(make_payload("replace_string_in_file", f.name))
            assert code == 0
            if out:
                parsed = json.loads(out)
                msg = parsed.get("systemMessage", "")
                assert (
                    "confession" not in msg.lower()
                ), f"unexpected confession warning on clean file: {msg}"
        finally:
            os.unlink(f.name)


# ── Runner ────────────────────────────────────────────────────────────

# ── Audit logging tests (FR-414) ──────────────────────────────────────


def test_non_edit_tool_no_audit_log():
    """Non-edit tools should NOT produce an audit log (PreToolUse logs them)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code, out = run_hook(
            {"toolName": "read_file", "toolInput": {"filePath": "foo.py"}},
            log_dir=tmpdir,
        )
        assert code == 0
        entries = read_audit_log(tmpdir)
        assert (
            len(entries) == 0
        ), f"non-edit tools should not be logged by post-edit, got: {entries}"


def test_clean_py_logs_approve():
    """A clean .py file should produce an approve/all-checks-clean audit entry."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\ny = 2\n")
        f.flush()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                code, out = run_hook(
                    make_payload("replace_string_in_file", f.name), log_dir=tmpdir
                )
                assert code == 0
                entries = read_audit_log(tmpdir)
                assert (
                    len(entries) >= 1
                ), f"expected audit log entry, got {len(entries)}"
                e = entries[-1]
                assert e["decision"] == "approve", f"expected approve, got: {e}"
                assert (
                    e["reason"] == "all-checks-clean"
                ), f"expected all-checks-clean, got: {e}"
                assert e["hook"] == "post-edit-checks", f"wrong hook: {e}"
        finally:
            os.unlink(f.name)


def test_issues_log_feedback():
    """A .py file with issues should produce a feedback audit entry."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1  # TODO: fix this\n")
        f.flush()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                code, out = run_hook(
                    make_payload("replace_string_in_file", f.name), log_dir=tmpdir
                )
                assert code == 0
                entries = read_audit_log(tmpdir)
                assert (
                    len(entries) >= 1
                ), f"expected audit log entry, got {len(entries)}"
                e = entries[-1]
                assert e["decision"] == "feedback", f"expected feedback, got: {e}"
                assert "ts" in e, f"missing timestamp: {e}"
        finally:
            os.unlink(f.name)


def test_ruff_missing_logs_error():
    """When ruff is not in PATH, should log error/ruff-missing."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\ny = 2\n")
        f.flush()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Run with PATH that doesn't include ruff
                payload = make_payload("replace_string_in_file", f.name)
                inp = json.dumps(payload)
                env = {
                    "PATH": "/usr/bin:/bin",
                    "HOME": os.environ["HOME"],
                    "HOOK_LOG_DIR": tmpdir,
                }
                r = subprocess.run(
                    [str(HOOK)],
                    input=inp,
                    capture_output=True,
                    text=True,
                    env=env,
                )
                assert r.returncode == 0
                entries = read_audit_log(tmpdir)
                # Should have at least one entry; check for ruff-missing
                ruff_missing = [e for e in entries if e.get("reason") == "ruff-missing"]
                assert (
                    len(ruff_missing) >= 1
                ), f"expected ruff-missing audit entry, got entries: {entries}"
                assert (
                    ruff_missing[0]["decision"] == "error"
                ), f"expected error decision: {ruff_missing[0]}"
        finally:
            os.unlink(f.name)


ALL_TESTS = [
    test_skips_non_edit_tools,
    test_skips_non_python_files,
    test_graph_yaml_invalid_reports_lint_errors,
    test_graph_yaml_valid_no_message,
    test_prompt_yaml_parse_error_reported,
    test_prompt_yaml_valid_no_message,
    test_ruff_lint_catches_errors,
    test_ruff_format_catches_issues,
    test_forbid_terms_catches_todo,
    test_forbid_terms_catches_fixme,
    test_forbid_terms_catches_backward_compat,
    test_file_size_warns_over_400,
    test_file_size_errors_over_450,
    test_debug_breakpoint,
    test_debug_pdb_import,
    test_clean_file_no_message,
    test_multi_replace_extracts_filepath,
    test_noqa_undocumented_flagged,
    test_noqa_blanket_flagged,
    test_no_noqa_no_warning,
    # FR-414 audit logging
    test_non_edit_tool_no_audit_log,
    test_clean_py_logs_approve,
    test_issues_log_feedback,
    test_ruff_missing_logs_error,
]


def main() -> int:
    passed = 0
    failed = 0
    for test in ALL_TESTS:
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
