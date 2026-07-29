#!/usr/bin/env python3
"""Tests for the FR-767 graph-authoring sole-route guard.

Covers the PreToolUse denial of unsentineled writes to governed graph
artifact paths (AC-07), sentinel scoping (AC-06, no global leakage,
R-1), terminal bypass shapes (R-3), and fail-closed ambiguity (C-5).

Infrastructure test scope (FR-436): outside REQ-YG marker coverage.

Run:  pytest .github/hooks/tests/test_authoring_guard.py -q --no-cov
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "pre-command-guard.sh"
pytestmark = pytest.mark.req("REQ-YG-527")

GOVERNED_CREATE = "examples/demos/zodiac/graph.yaml"
GOVERNED_PROMPT = "examples/demos/zodiac/prompts/sign.yaml"
GOVERNED_TRACKED = "examples/demos/hello/graph.yaml"
GOVERNED_TOP = "graphs/showcase.yaml"
GOVERNED_CHAPLAIN = ".chaplain/graphs/pipeline.yaml"
UNGOVERNED = "docs/notes.md"


def run_hook(payload, *, env_extra=None, log_dir=None):
    env = {**os.environ}
    env.pop("YAMLGRAPH_AUTHORING_TOKEN", None)
    if env_extra:
        env.update(env_extra)
    if log_dir:
        env["HOOK_LOG_DIR"] = log_dir
    r = subprocess.run(
        [str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return r.returncode, r.stdout.strip()


def decision_of(stdout: str) -> str:
    d = json.loads(stdout)
    if d.get("decision") == "approve":
        return "approve"
    return d.get("hookSpecificOutput", {}).get("permissionDecision", "unknown")


def edit_payload(tool, file_path):
    if tool == "multi_replace_string_in_file":
        tool_input = {"replacements": [{"filePath": file_path}]}
    elif tool == "apply_patch":
        tool_input = {"input": f"*** Add File: {file_path}\n+content"}
    else:
        tool_input = {"filePath": file_path}
    return {"tool_name": tool, "tool_input": tool_input, "session_id": "s1"}


def terminal_payload(command):
    return {
        "tool_name": "run_in_terminal",
        "tool_input": {"command": command},
        "session_id": "s1",
    }


@pytest.fixture
def sentinel(tmp_path):
    """Armed sentinel + matching env token, mimicking author.sh."""
    run_id = "tok-fr767-test"
    sentinel_file = tmp_path / ".authoring-sentinel"
    sentinel_file.write_text(json.dumps({"token": run_id, "pid": 1}))
    return {
        "YAMLGRAPH_AUTHORING_TOKEN": run_id,
        "YAMLGRAPH_AUTHORING_SENTINEL": str(sentinel_file),
    }


# ── Deny without sentinel: file-write tools (AC-07) ──────────────────


@pytest.mark.parametrize(
    "tool",
    [
        "create_file",
        "replace_string_in_file",
        "multi_replace_string_in_file",
        "apply_patch",
    ],
)
def test_deny_unsentineled_governed_write(tool):
    rc, out = run_hook(edit_payload(tool, GOVERNED_CREATE))
    assert rc == 0
    assert decision_of(out) == "deny"
    assert "author.sh" in out


@pytest.mark.parametrize(
    "path",
    [
        GOVERNED_CREATE,
        GOVERNED_PROMPT,
        GOVERNED_TRACKED,
        GOVERNED_TOP,
        GOVERNED_CHAPLAIN,
    ],
)
def test_deny_covers_all_governed_paths(path):
    rc, out = run_hook(edit_payload("create_file", path))
    assert decision_of(out) == "deny"


def test_deny_existing_tracked_governed_artifact():
    """R-2 bright line: tracked governed artifacts are denied too."""
    rc, out = run_hook(edit_payload("replace_string_in_file", GOVERNED_TRACKED))
    assert decision_of(out) == "deny"


def test_approve_ungoverned_write():
    rc, out = run_hook(edit_payload("create_file", UNGOVERNED))
    assert decision_of(out) == "approve"


def test_approve_ungoverned_yaml():
    """Prompt YAML outside governed trees is not the guard's business."""
    rc, out = run_hook(edit_payload("create_file", "prompts/summarize.yaml"))
    assert decision_of(out) == "approve"


# ── Deny without sentinel: terminal surface (R-3) ────────────────────


@pytest.mark.parametrize(
    "command",
    [
        "cp -r examples/demos/hello examples/demos/zodiac",
        f"cp examples/demos/hello/graph.yaml {GOVERNED_CREATE}",
        f"mv tmp/draft.yaml {GOVERNED_CREATE}",
        f"echo 'nodes:' > {GOVERNED_CREATE}",
        f"printf 'nodes:' >> {GOVERNED_CREATE}",
        f"tee {GOVERNED_CREATE} < tmp/x.yaml",
        f"cat <<EOF > {GOVERNED_CREATE}\nnodes:\nEOF",
        f'echo "nodes:" > "{GOVERNED_CREATE}"',  # quoted path variant
    ],
)
def test_deny_terminal_write_shapes(command):
    rc, out = run_hook(terminal_payload(command))
    assert decision_of(out) == "deny"
    assert "author.sh" in out


def test_approve_terminal_read_of_governed_path():
    rc, out = run_hook(terminal_payload(f"cat {GOVERNED_TRACKED}"))
    assert decision_of(out) == "approve"


def test_approve_terminal_lint_of_governed_path():
    rc, out = run_hook(terminal_payload(f"yamlgraph graph lint {GOVERNED_TRACKED}"))
    assert decision_of(out) == "approve"


def test_approve_git_operations_on_governed_path():
    rc, out = run_hook(terminal_payload(f"git add {GOVERNED_TRACKED}"))
    assert decision_of(out) == "approve"


# ── Allow with sentinel (AC-06) ──────────────────────────────────────


@pytest.mark.parametrize(
    "tool", ["create_file", "replace_string_in_file", "apply_patch"]
)
def test_allow_sentineled_file_write(tool, sentinel):
    rc, out = run_hook(edit_payload(tool, GOVERNED_CREATE), env_extra=sentinel)
    assert decision_of(out) == "approve"


def test_allow_sentineled_terminal_write(sentinel):
    rc, out = run_hook(
        terminal_payload(f"cp tmp/draft.yaml {GOVERNED_CREATE}"),
        env_extra=sentinel,
    )
    assert decision_of(out) == "approve"


# ── Sentinel scoping: no global leakage (R-1, AC-08) ─────────────────


def test_deny_token_mismatch(sentinel):
    """Env token not matching sentinel token => deny (stolen/stale env)."""
    bad = {**sentinel, "YAMLGRAPH_AUTHORING_TOKEN": "wrong-token"}
    rc, out = run_hook(edit_payload("create_file", GOVERNED_CREATE), env_extra=bad)
    assert decision_of(out) == "deny"


def test_deny_sentinel_file_without_env_token(sentinel):
    """Sentinel file alone (another session's run) must not allow."""
    env = {"YAMLGRAPH_AUTHORING_SENTINEL": sentinel["YAMLGRAPH_AUTHORING_SENTINEL"]}
    rc, out = run_hook(edit_payload("create_file", GOVERNED_CREATE), env_extra=env)
    assert decision_of(out) == "deny"


def test_deny_env_token_without_sentinel_file(tmp_path):
    """Env token pointing at a removed sentinel (expired run) => deny."""
    env = {
        "YAMLGRAPH_AUTHORING_TOKEN": "tok",
        "YAMLGRAPH_AUTHORING_SENTINEL": str(tmp_path / "gone"),
    }
    rc, out = run_hook(edit_payload("create_file", GOVERNED_CREATE), env_extra=env)
    assert decision_of(out) == "deny"


# ── Fail closed on ambiguity (C-5) ───────────────────────────────────


def test_deny_ambiguous_terminal_write():
    """Unparseable write shape touching a governed path: deny, not approve."""
    rc, out = run_hook(
        terminal_payload(f'python3 -c \'open("{GOVERNED_CREATE}","w").write("x")\'')
    )
    assert decision_of(out) == "deny"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q", "--no-cov"]))
