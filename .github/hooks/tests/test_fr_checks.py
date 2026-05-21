#!/usr/bin/env python3
"""Tests for modular feature-request post-edit checks."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from conftest import make_apply_patch_payload, make_payload, run_hook


def test_skips_non_edit_tools() -> None:
    code, out = run_hook(
        "fr-checks.sh",
        {"toolName": "read_file", "toolInput": {"filePath": "foo.md"}},
    )
    assert code == 0
    assert "systemMessage" not in out


def test_feature_request_fsm_reinvention_warns() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = Path(tmpdir) / "feature-requests"
        fr_dir.mkdir(parents=True, exist_ok=True)
        fr_file = fr_dir / "FR-test.md"
        fr_file.write_text(
            "We should build a state machine for lifecycle management.\n"
            "Use event-driven workflow and explicit transition guard logic.\n",
            encoding="utf-8",
        )

        code, out = run_hook(
            "fr-checks.sh", make_payload("replace_string_in_file", str(fr_file))
        )
        assert code == 0
        parsed = json.loads(out)
        msg = parsed.get("systemMessage", "")
        assert "fsm patterns detected" in msg.lower()


def test_feature_request_fsm_escape_hatch_clean() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        fr_dir = Path(tmpdir) / "feature-requests"
        fr_dir.mkdir(parents=True, exist_ok=True)
        fr_file = fr_dir / "FR-test.md"
        fr_file.write_text(
            "Use statemachine_engine with event-driven workflow.\n"
            "This FSM integration already exists in yamlgraph/utils/fsm.\n",
            encoding="utf-8",
        )

        code, out = run_hook(
            "fr-checks.sh", make_payload("replace_string_in_file", str(fr_file))
        )
        assert code == 0
        if out:
            parsed = json.loads(out)
            msg = parsed.get("systemMessage", "")
            assert "fsm patterns detected" not in msg.lower()


def test_apply_patch_non_fr_markdown_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "notes.md"
        md_file.write_text("state machine mention\n", encoding="utf-8")

        payload = make_apply_patch_payload([str(md_file)])
        code, out = run_hook("fr-checks.sh", payload)
        assert code == 0
        assert "systemMessage" not in out
