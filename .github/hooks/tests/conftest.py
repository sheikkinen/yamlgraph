#!/usr/bin/env python3
"""Shared helpers for modular post-edit hook tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
CHECKS_DIR = HOOKS_ROOT / "scripts" / "checks"


def run_hook(
    script_name: str,
    payload: dict,
    *,
    log_dir: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Run a modular check script with JSON payload, return (exit_code, stdout)."""
    inp = json.dumps(payload)
    env = {**os.environ, "PATH": f".venv/bin:{os.environ.get('PATH', '')}"}
    if log_dir:
        env["HOOK_LOG_DIR"] = log_dir
    if extra_env:
        env.update(extra_env)
    script = CHECKS_DIR / script_name
    r = subprocess.run(
        [str(script)],
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


def make_apply_patch_payload(file_paths: list[str]) -> dict:
    """Build an apply_patch payload touching provided files."""
    lines = ["*** Begin Patch"]
    for file_path in file_paths:
        lines.extend(
            [
                f"*** Update File: {file_path}",
                "@@",
                "-old",
                "+new",
            ]
        )
    lines.append("*** End Patch")
    return {"toolName": "apply_patch", "toolInput": {"input": "\n".join(lines)}}
