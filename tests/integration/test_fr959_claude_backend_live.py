"""FR-959 AC-14/AC-15: disposable two-node live witness for ``backend: claude``.

Judgement R-6: this harness builds a temporary graph in ``tmp_path`` — two
``type: copilot`` / ``backend: claude`` nodes, no tools, one-word prompts, the
second node resuming the first node's real ``session_id``. The committed
``examples/demos/session-continuation/**`` is neither modified nor executed.

Gated: runs only with ``YAMLGRAPH_LIVE_CLAUDE=1`` on a host where ``claude``
(the pinned version) is on PATH and logged in on a subscription. Bills the
operator's Claude subscription for two tiny turns. The witness record goes to
``feature-requests/evidence/FR-959-claude-backend-witness.md`` (hand-written
from the printed argv/IDs; this test prints everything the record needs).
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("YAMLGRAPH_LIVE_CLAUDE") != "1",
    reason="live Claude Code witness; set YAMLGRAPH_LIVE_CLAUDE=1 on a subscription host",
)

GRAPH = """\
version: "1.0"
name: fr959-live-witness
prompts_relative: true
prompts_dir: prompts
state:
  first: dict
  second: dict
nodes:
  first:
    type: copilot
    backend: claude
    cli_flags: {tools: []}
    prompt: first
    state_key: first
    timeout: 120
  second:
    type: copilot
    backend: claude
    cli_flags: {tools: [], resume: "{state.first.session_id}"}
    prompt: second
    state_key: second
    timeout: 120
edges:
  - {from: START, to: first}
  - {from: first, to: second}
  - {from: second, to: END}
"""
PROMPT_FIRST = "user: Reply with the single word pong and nothing else.\n"
PROMPT_SECOND = (
    "user: Reply with the single word you replied with before, nothing else.\n"
)


def _write_graph(root: Path) -> Path:
    (root / "prompts").mkdir()
    (root / "prompts" / "first.yaml").write_text(PROMPT_FIRST, encoding="utf-8")
    (root / "prompts" / "second.yaml").write_text(PROMPT_SECOND, encoding="utf-8")
    graph = root / "graph.yaml"
    graph.write_text(GRAPH, encoding="utf-8")
    return graph


@pytest.mark.req("REQ-YG-641")
def test_two_node_resume_carries_real_session_id(tmp_path: Path, capsys) -> None:
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    graph = _write_graph(tmp_path)
    digest = hashlib.sha256(graph.read_bytes()).hexdigest()
    argvs: list[list[str]] = []
    real_run = subprocess.run

    def spy(cmd, *a, **kw):
        argvs.append(list(cmd))
        return real_run(cmd, *a, **kw)

    started = datetime.now(UTC).isoformat()
    with patch("subprocess.run", side_effect=spy):
        app = compile_graph(load_graph_config(graph)).compile()
        final = app.invoke({})
    ended = datetime.now(UTC).isoformat()

    first, second = final["first"], final["second"]
    assert first.backend == "claude" and second.backend == "claude"
    assert first.session_id, "first node must return a real session_id"
    agent_argvs = [a for a in argvs if a[:2] == ["claude", "-p"]]
    assert len(agent_argvs) == 2
    assert "--resume" in agent_argvs[1]
    assert agent_argvs[1][agent_argvs[1].index("--resume") + 1] == first.session_id
    assert (
        "--tools" in agent_argvs[0]
        and agent_argvs[0][agent_argvs[0].index("--tools") + 1] == ""
    )

    # Everything the witness record needs, redacted (prompts are public text).
    print("\n=== FR-959 live witness ===")
    print(f"started={started} ended={ended}")
    print(f"temp graph sha256={digest}")
    print(
        f"env ANTHROPIC_API_KEY present in parent={'ANTHROPIC_API_KEY' in os.environ}"
    )
    for i, a in enumerate(argvs):
        print(f"argv[{i}]={a}")
    print(f"first.session_id={first.session_id} first.output={first.output[:60]!r}")
    print(f"second.session_id={second.session_id} second.output={second.output[:60]!r}")
    assert capsys is not None
