#!/usr/bin/env python3
"""Tests for the FR-767 graph-authoring sole-route guard.

Covers the PreToolUse denial of unsentineled writes to governed graph
artifact paths (AC-07), sentinel scoping (AC-06, no global leakage,
R-1), terminal bypass shapes (R-3), and fail-closed ambiguity (C-5).

Infrastructure test scope (FR-436): outside req_coverage's scan. Markers
are declared per test anyway: FR-767 route tests carry REQ-YG-527; the
FR-1014 dir-aware ``graphs/`` truth table carries REQ-YG-423 (CAP-158,
the requirement that owns the executable graph-authoring route).

FR-1014 truth table (shared with tests/unit/test_fr1014_authoring_proof_dir_graphs.py):
every positive is denied without a sentinel, every negative is approved.
Provenance is labelled on each constant; synthetic rows are never cited
as evidence of the current tree (FR-1014 R-2).

Run:  pytest .github/hooks/tests/test_authoring_guard.py -q --no-cov
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "pre-command-guard.sh"
_REQ_FR767 = pytest.mark.req("REQ-YG-527")
_REQ_FR1014 = pytest.mark.req("REQ-YG-423")

GOVERNED_CREATE = "examples/demos/zodiac/graph.yaml"
GOVERNED_PROMPT = "examples/demos/zodiac/prompts/sign.yaml"
GOVERNED_TRACKED = "examples/demos/hello/graph.yaml"
UNGOVERNED = "docs/notes.md"

# ── FR-1014 truth table: graphs/ arm, dir-aware ──────────────────────
# Provenance labels (R-2): "exists" rows pass `git ls-files --error-unmatch`
# on main (the fr_triage rows since FR-1011 relocated them); "synthetic" rows exercise a contract arm with no committed
# instance and are never cited as evidence of the current tree.
GOVERNED_FLAT_SYNTHETIC = "graphs/fr1014-flat.yaml"  # synthetic: flat arm
GOVERNED_DIR_DIRECT_EXISTS = "graphs/enforcement/changelog-req-check.yaml"  # exists
GOVERNED_DIR_PROMPT_EXISTS = "graphs/enforcement/prompts/cross_check.yaml"  # exists
GOVERNED_DIR_GRAPH_FR1011 = "graphs/fr_triage/graph.yaml"  # exists (relocated by FR-1011)
GOVERNED_DIR_PROMPT_FR1011 = "graphs/fr_triage/prompts/triage_fr.yaml"  # exists (relocated by FR-1011)

FR1014_POSITIVES = [
    GOVERNED_DIR_DIRECT_EXISTS,
    GOVERNED_DIR_PROMPT_EXISTS,
    GOVERNED_DIR_GRAPH_FR1011,
    GOVERNED_DIR_PROMPT_FR1011,
    GOVERNED_FLAT_SYNTHETIC,
]
FR1014_NEGATIVES = [
    "graphs/README.md",  # negative: not YAML
    "graphs/fr_triage/tools.py",  # negative: not YAML
    "graphs/fr_triage/nested/graph.yaml",  # negative: depth > 1
    "graphs/fr_triage/prompts/nested/triage.yaml",  # negative: depth > 1
]


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
    sentinel_file.write_text(json.dumps({"token": run_id, "pid": 1}), encoding="utf-8")
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
@_REQ_FR767
def test_deny_unsentineled_governed_write(tool):
    rc, out = run_hook(edit_payload(tool, GOVERNED_CREATE))
    assert rc == 0
    assert decision_of(out) == "deny"
    assert "author.sh" in out


@pytest.mark.parametrize(
    "path",
    [GOVERNED_CREATE, GOVERNED_PROMPT, GOVERNED_TRACKED, *FR1014_POSITIVES],
)
@_REQ_FR1014
def test_deny_covers_all_governed_paths(path):
    """FR-767 examples/ arms plus the FR-1014 graphs/ truth-table positives.

    Denial must name the sole route (FR-1014 AC-06, AC-11).
    """
    rc, out = run_hook(edit_payload("create_file", path))
    assert decision_of(out) == "deny"
    assert "author.sh" in out


@pytest.mark.parametrize("path", FR1014_NEGATIVES)
@_REQ_FR1014
def test_approve_ungoverned_graphs_dir_paths(path):
    """FR-1014 negatives: non-YAML and depth > 1 under graphs/ stay ungoverned."""
    rc, out = run_hook(edit_payload("create_file", path))
    assert decision_of(out) == "approve"


@_REQ_FR767
def test_deny_existing_tracked_governed_artifact():
    """R-2 bright line: tracked governed artifacts are denied too."""
    rc, out = run_hook(edit_payload("replace_string_in_file", GOVERNED_TRACKED))
    assert decision_of(out) == "deny"


@_REQ_FR767
def test_approve_ungoverned_write():
    rc, out = run_hook(edit_payload("create_file", UNGOVERNED))
    assert decision_of(out) == "approve"


@_REQ_FR767
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
@_REQ_FR767
def test_deny_terminal_write_shapes(command):
    rc, out = run_hook(terminal_payload(command))
    assert decision_of(out) == "deny"
    assert "author.sh" in out


@_REQ_FR767
def test_approve_terminal_read_of_governed_path():
    rc, out = run_hook(terminal_payload(f"cat {GOVERNED_TRACKED}"))
    assert decision_of(out) == "approve"


@_REQ_FR767
def test_approve_terminal_lint_of_governed_path():
    rc, out = run_hook(terminal_payload(f"yamlgraph graph lint {GOVERNED_TRACKED}"))
    assert decision_of(out) == "approve"


@_REQ_FR767
def test_approve_git_operations_on_governed_path():
    rc, out = run_hook(terminal_payload(f"git add {GOVERNED_TRACKED}"))
    assert decision_of(out) == "approve"


# ── Allow with sentinel (AC-06) ──────────────────────────────────────


@pytest.mark.parametrize(
    "tool", ["create_file", "replace_string_in_file", "apply_patch"]
)
@_REQ_FR767
def test_allow_sentineled_file_write(tool, sentinel):
    rc, out = run_hook(edit_payload(tool, GOVERNED_CREATE), env_extra=sentinel)
    assert decision_of(out) == "approve"


@_REQ_FR767
def test_allow_sentineled_terminal_write(sentinel):
    rc, out = run_hook(
        terminal_payload(f"cp tmp/draft.yaml {GOVERNED_CREATE}"),
        env_extra=sentinel,
    )
    assert decision_of(out) == "approve"


# ── Sentinel scoping: no global leakage (R-1, AC-08) ─────────────────


@_REQ_FR767
def test_deny_token_mismatch(sentinel):
    """Env token not matching sentinel token => deny (stolen/stale env)."""
    bad = {**sentinel, "YAMLGRAPH_AUTHORING_TOKEN": "wrong-token"}
    rc, out = run_hook(edit_payload("create_file", GOVERNED_CREATE), env_extra=bad)
    assert decision_of(out) == "deny"


@_REQ_FR767
def test_deny_sentinel_file_without_env_token(sentinel):
    """Sentinel file alone (another session's run) must not allow."""
    env = {"YAMLGRAPH_AUTHORING_SENTINEL": sentinel["YAMLGRAPH_AUTHORING_SENTINEL"]}
    rc, out = run_hook(edit_payload("create_file", GOVERNED_CREATE), env_extra=env)
    assert decision_of(out) == "deny"


@_REQ_FR767
def test_deny_env_token_without_sentinel_file(tmp_path):
    """Env token pointing at a removed sentinel (expired run) => deny."""
    env = {
        "YAMLGRAPH_AUTHORING_TOKEN": "tok",
        "YAMLGRAPH_AUTHORING_SENTINEL": str(tmp_path / "gone"),
    }
    rc, out = run_hook(edit_payload("create_file", GOVERNED_CREATE), env_extra=env)
    assert decision_of(out) == "deny"


# ── Fail closed on ambiguity (C-5) ───────────────────────────────────


@_REQ_FR767
def test_deny_ambiguous_terminal_write():
    """Unparseable write shape touching a governed path: deny, not approve."""
    rc, out = run_hook(
        terminal_payload(f'python3 -c \'open("{GOVERNED_CREATE}","w").write("x")\'')
    )
    assert decision_of(out) == "deny"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q", "--no-cov"]))
