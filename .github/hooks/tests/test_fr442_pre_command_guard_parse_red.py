#!/usr/bin/env python3
"""FR-442 acceptance tests for pre-command-guard parse consolidation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "pre-command-guard.sh"


def _parse_block() -> str:
    text = HOOK.read_text(encoding="utf-8")
    start = text.index("# ── Parse input (fail-closed)")
    end = text.index("# ── Lockdown check")
    return text[start:end]


def _run_hook_with_python_counter(
    payload: dict, tmp_path: Path
) -> tuple[int, str, int]:
    real_python = shutil.which("python3")
    assert real_python, "python3 not found"

    counter_file = tmp_path / "python-count.txt"
    counter_file.write_text("0", encoding="utf-8")

    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    shim = shim_dir / "python3"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'counter="${HOOK_PY_COUNTER_FILE:?}"\n'
        "current=0\n"
        'if [[ -f "$counter" ]]; then\n'
        '  current=$(cat "$counter")\n'
        "fi\n"
        'printf "%s" "$((current + 1))" > "$counter"\n'
        f'exec "{real_python}" "$@"\n'
    , encoding="utf-8")
    shim.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}:{env.get('PATH', '')}"
    env["HOOK_PY_COUNTER_FILE"] = str(counter_file)
    env["HOOK_LOG_DIR"] = str(tmp_path / "logs")

    result = subprocess.run(
        [str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )

    count = int(counter_file.read_text(encoding="utf-8").strip() or "0")
    return result.returncode, result.stdout.strip(), count


@pytest.mark.req("REQ-YG-063")
def test_ac01_parse_block_uses_single_python_invocation():
    parse_block = _parse_block()
    assert parse_block.count("python3 -c") == 1


@pytest.mark.req("REQ-YG-063")
def test_ac02_parse_block_has_no_reparse_of_parsed_json():
    parse_block = _parse_block()
    assert 'echo "$PARSED" | python3 -c' not in parse_block


@pytest.mark.req("REQ-YG-063")
def test_ac03_common_non_terminal_path_python_invocations_within_budget(tmp_path: Path):
    payload = {"toolName": "read_file", "toolInput": {"path": "foo.py"}}
    code, out, count = _run_hook_with_python_counter(payload, tmp_path)
    assert code == 0
    assert '"decision":"approve"' in out
    assert count <= 3, f"expected <=3 python invocations, got {count}"


@pytest.mark.req("REQ-YG-063")
def test_ac04_terminal_clean_path_python_invocations_within_budget(tmp_path: Path):
    payload = {"toolName": "run_in_terminal", "toolInput": {"command": "git add ."}}
    code, out, count = _run_hook_with_python_counter(payload, tmp_path)
    assert code == 0
    assert '"decision":"approve"' in out
    assert count <= 3, f"expected <=3 python invocations, got {count}"
