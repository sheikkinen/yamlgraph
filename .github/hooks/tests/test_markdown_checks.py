#!/usr/bin/env python3
"""Tests for modular markdown post-edit checks."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from conftest import make_apply_patch_payload, make_payload, read_audit_log, run_hook


def test_skips_non_edit_tools() -> None:
    code, out = run_hook(
        "markdown-checks.sh",
        {"toolName": "read_file", "toolInput": {"filePath": "foo.md"}},
    )
    assert code == 0
    assert "systemMessage" not in out


def test_skips_non_markdown_files() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\n")
        f.flush()
        code, out = run_hook(
            "markdown-checks.sh", make_payload("replace_string_in_file", f.name)
        )
        assert code == 0
        assert "systemMessage" not in out


def test_markdown_trailing_whitespace_warns_default_mode() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".md", mode="w", delete=False) as f:
        f.write("# Title  \n")
        f.flush()
        path = Path(f.name)

    code, out = run_hook(
        "markdown-checks.sh", make_payload("replace_string_in_file", str(path))
    )
    assert code == 0
    parsed = json.loads(out)
    msg = parsed.get("systemMessage", "")
    assert "trailing whitespace" in msg.lower()
    assert f"File: {path}" in msg


def test_markdown_trailing_whitespace_autofix_enabled() -> None:
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".md", mode="w", delete=False) as f:
        original = "# Title  \nLine two   \n"
        f.write(original)
        f.flush()
        path = Path(f.name)

    with tempfile.TemporaryDirectory() as tmpdir:
        code, out = run_hook(
            "markdown-checks.sh",
            make_payload("replace_string_in_file", str(path)),
            log_dir=tmpdir,
            extra_env={"POST_EDIT_AUTO_MD": "1"},
        )
        assert code == 0
        current = path.read_text(encoding="utf-8")
        assert current == "# Title\nLine two\n"

        if out:
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "trailing whitespace" not in msg.lower()

        entries = read_audit_log(tmpdir)
        autofix_entries = [
            e for e in entries if e.get("reason") == "markdown-autofix-applied"
        ]
        assert len(autofix_entries) >= 1


def test_apply_patch_mixed_files_reports_only_markdown_targets() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "notes.md"
        py_file = Path(tmpdir) / "x.py"
        md_file.write_text("line with space  \n", encoding="utf-8")
        py_file.write_text("x = 1\n", encoding="utf-8")

        payload = make_apply_patch_payload([str(md_file), str(py_file)])
        code, out = run_hook("markdown-checks.sh", payload)
        assert code == 0
        parsed = json.loads(out)
        msg = parsed.get("systemMessage", "")
        assert f"File: {md_file}" in msg
        assert f"File: {py_file}" not in msg


def test_feature_requests_markdown_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = Path(tmpdir) / "feature-requests"
        fr_dir.mkdir(parents=True, exist_ok=True)
        fr_file = fr_dir / "FR-test.md"
        fr_file.write_text("line with space  \n", encoding="utf-8")

        code, out = run_hook(
            "markdown-checks.sh", make_payload("replace_string_in_file", str(fr_file))
        )
        assert code == 0
        assert "systemMessage" not in out
