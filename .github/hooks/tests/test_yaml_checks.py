#!/usr/bin/env python3
"""Tests for modular YAML post-edit checks."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from conftest import make_apply_patch_payload, make_payload, run_hook


def test_skips_non_edit_tools() -> None:
    code, out = run_hook(
        "yaml-checks.sh",
        {"toolName": "read_file", "toolInput": {"filePath": "foo.yaml"}},
    )
    assert code == 0
    assert "systemMessage" not in out


def test_skips_non_yaml_files() -> None:
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1\n")
        f.flush()
        try:
            code, out = run_hook(
                "yaml-checks.sh", make_payload("replace_string_in_file", f.name)
            )
            assert code == 0
            assert "systemMessage" not in out
        finally:
            os.unlink(f.name)


def test_graph_yaml_invalid_reports_lint_errors() -> None:
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
            code, out = run_hook(
                "yaml-checks.sh", make_payload("replace_string_in_file", f.name)
            )
            assert code == 0
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "graph lint issues" in msg.lower()
        finally:
            os.unlink(f.name)


def test_graph_yaml_valid_no_message() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    graph_path = repo_root / "examples" / "demos" / "hello" / "graph.yaml"
    code, out = run_hook(
        "yaml-checks.sh", make_payload("replace_string_in_file", str(graph_path))
    )
    assert code == 0
    if out:
        parsed = json.loads(out)
        msg = parsed.get("systemMessage", "")
        assert msg == ""


def test_prompt_yaml_parse_error_reported() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_dir = Path(tmpdir) / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / "bad.yaml"
        prompt_file.write_text("template: [broken\n", encoding="utf-8")

        code, out = run_hook(
            "yaml-checks.sh", make_payload("replace_string_in_file", str(prompt_file))
        )
        assert code == 0
        parsed = json.loads(out)
        msg = parsed.get("systemMessage", "")
        assert "prompt file error" in msg.lower()


def test_apply_patch_mixed_files_only_reports_yaml() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_dir = Path(tmpdir) / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        py_file = Path(tmpdir) / "x.py"
        bad_prompt = prompt_dir / "bad.yaml"
        py_file.write_text("x=1\n", encoding="utf-8")
        bad_prompt.write_text("template: [broken\n", encoding="utf-8")

        payload = make_apply_patch_payload([str(py_file), str(bad_prompt)])
        code, out = run_hook("yaml-checks.sh", payload)
        assert code == 0
        parsed = json.loads(out)
        msg = parsed.get("systemMessage", "")
        assert f"File: {bad_prompt}" in msg
        assert f"File: {py_file}" not in msg
