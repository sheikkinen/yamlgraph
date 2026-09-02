#!/usr/bin/env python3
"""Tests for modular Python post-edit checks."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from conftest import (
    CHECKS_DIR,
    HOOKS_ROOT,
    make_apply_patch_payload,
    make_payload,
    read_audit_log,
    run_hook,
)


def _fixture_ruff(tmpdir: str) -> str:
    """Symlink a real ruff into tmpdir as a deterministic fixture path (FR-793 R-4)."""
    real = shutil.which("ruff") or str(HOOKS_ROOT.parents[1] / ".venv" / "bin" / "ruff")
    if not Path(real).is_file():
        pytest.skip("no ruff available to build fixture")
    link = Path(tmpdir) / "ruff"
    link.symlink_to(real)
    return str(link)


def _run_hook_bare_env(
    payload: dict, log_dir: str, extra_env: dict[str, str] | None = None
) -> tuple[int, str]:
    """Run python-checks.sh with a stripped PATH (no venv, no ruff)."""
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": os.environ["HOME"],
        "HOOK_LOG_DIR": log_dir,
    }
    if extra_env:
        env.update(extra_env)
    r = subprocess.run(
        [str(CHECKS_DIR / "python-checks.sh")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return r.returncode, r.stdout.strip()


def test_skips_non_edit_tools() -> None:
    code, out = run_hook(
        "python-checks.sh",
        {"toolName": "read_file", "toolInput": {"filePath": "foo.py"}},
    )
    assert code == 0
    assert "systemMessage" not in out


def test_clean_file_no_message() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\ny = 2\n")
        f.flush()
        try:
            code, out = run_hook(
                "python-checks.sh", make_payload("replace_string_in_file", f.name)
            )
            assert code == 0
            if out:
                parsed = json.loads(out)
                assert parsed.get("systemMessage", "") == ""
        finally:
            os.unlink(f.name)


def test_ruff_lint_catches_errors() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        f.write("import os\nimport sys\n\nx = 1\n")
        f.flush()
        try:
            code, out = run_hook(
                "python-checks.sh", make_payload("create_file", f.name)
            )
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "ruff" in msg.lower() or "F401" in msg
        finally:
            os.unlink(f.name)


def test_file_size_errors_over_450() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\n" * 460)
        f.flush()
        try:
            code, out = run_hook(
                "python-checks.sh", make_payload("replace_string_in_file", f.name)
            )
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "460" in msg or "450" in msg
        finally:
            os.unlink(f.name)


def test_debug_breakpoint() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\nbreakpoint()\ny = 2\n")
        f.flush()
        try:
            code, out = run_hook(
                "python-checks.sh", make_payload("replace_string_in_file", f.name)
            )
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "breakpoint" in msg or "debug" in msg.lower()
        finally:
            os.unlink(f.name)


def test_apply_patch_aggregates_multi_file_issues() -> None:
    with (
        tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f1,
        tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f2,
    ):
        f1.write("x = 1  # TODO: remove\n")
        f2.write("import pdb\npdb.set_trace()\n")
        f1.flush()
        f2.flush()
        try:
            payload = make_apply_patch_payload([f1.name, f2.name])
            code, out = run_hook("python-checks.sh", payload)
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert f"File: {f1.name}" in msg
            assert f"File: {f2.name}" in msg
        finally:
            os.unlink(f1.name)
            os.unlink(f2.name)


def test_apply_patch_autofix_enabled_applies_ruff_fixes() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        original = "import os\nx=1\n"
        f.write(original)
        f.flush()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                payload = make_apply_patch_payload([f.name])
                code, out = run_hook(
                    "python-checks.sh",
                    payload,
                    log_dir=tmpdir,
                    extra_env={"POST_EDIT_AUTO_RUFF": "1"},
                )
                assert code == 0
                current = Path(f.name).read_text(encoding="utf-8")
                assert current != original

                if out:
                    parsed = json.loads(out)
                    msg = parsed.get("systemMessage", "")
                    assert "F401" not in msg

                entries = read_audit_log(tmpdir)
                autofix_entries = [
                    e for e in entries if e.get("reason") == "ruff-autofix-applied"
                ]
                assert len(autofix_entries) >= 1
        finally:
            os.unlink(f.name)


def test_ruff_missing_logs_error() -> None:
    """AC-02 (FR-793): ruff absent from PATH and fallback -> exactly one entry per file."""
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\ny = 2\n")
        f.flush()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                payload = make_payload("replace_string_in_file", f.name)
                code, _ = _run_hook_bare_env(
                    payload,
                    tmpdir,
                    extra_env={"HOOK_RUFF_BIN": str(Path(tmpdir) / "absent-ruff")},
                )
                assert code == 0
                entries = read_audit_log(tmpdir)
                ruff_missing = [e for e in entries if e.get("reason") == "ruff-missing"]
                assert len(ruff_missing) == 1
                assert ruff_missing[0]["decision"] == "error"
        finally:
            os.unlink(f.name)


def test_ruff_resolved_from_fallback_when_path_missing() -> None:
    """AC-01 (FR-793): stripped PATH + fixture binary -> real ruff feedback, no ruff-missing."""
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        f.write("import os\nimport sys\n\nx = 1\n")
        f.flush()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                ruff_bin = _fixture_ruff(tmpdir)
                payload = make_payload("create_file", f.name)
                code, out = _run_hook_bare_env(
                    payload, tmpdir, extra_env={"HOOK_RUFF_BIN": ruff_bin}
                )
                assert code == 0
                parsed = json.loads(out)
                msg = parsed.get("systemMessage", "")
                assert "F401" in msg or "ruff" in msg.lower()
                entries = read_audit_log(tmpdir)
                assert not [e for e in entries if e.get("reason") == "ruff-missing"]
        finally:
            os.unlink(f.name)


def test_auto_ruff_uses_resolved_binary() -> None:
    """AC-03 (FR-793): POST_EDIT_AUTO_RUFF=1 works via the resolved binary."""
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        original = "import os\nx=1\n"
        f.write(original)
        f.flush()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                ruff_bin = _fixture_ruff(tmpdir)
                payload = make_payload("create_file", f.name)
                code, _ = _run_hook_bare_env(
                    payload,
                    tmpdir,
                    extra_env={
                        "HOOK_RUFF_BIN": ruff_bin,
                        "POST_EDIT_AUTO_RUFF": "1",
                    },
                )
                assert code == 0
                assert Path(f.name).read_text(encoding="utf-8") != original
                entries = read_audit_log(tmpdir)
                autofix = [
                    e for e in entries if e.get("reason") == "ruff-autofix-applied"
                ]
                assert len(autofix) >= 1
        finally:
            os.unlink(f.name)


def test_no_bare_ruff_invocations_in_script() -> None:
    """AC-04 (FR-793): all ruff invocations go through the resolved binary."""
    text = (CHECKS_DIR / "python-checks.sh").read_text(encoding="utf-8")
    assert "command -v ruff" not in text
    for line in text.splitlines():
        if re.search(r"\bruff (check|format)\b", line) and "Run:" not in line:
            assert '"$RUFF_BIN"' in line, f"bare ruff invocation: {line.strip()}"
