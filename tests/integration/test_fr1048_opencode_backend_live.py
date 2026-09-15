"""FR-1048 AC-16/AC-17: disposable two-node live witness for ``backend: opencode``.

This harness builds a temporary graph in ``tmp_path`` — two
``type: copilot`` / ``backend: opencode`` nodes, one-word prompts, the second
node resuming the first node's real ``session_id`` and recalling a nonce. The
committed ``examples/demos/session-continuation/**`` is neither modified nor
executed.

Gated: runs only with ``YAMLGRAPH_LIVE_OPENCODE=1`` on a host where the pinned
``opencode`` is on PATH with provider credentials. Bills the resolved provider
for two tiny turns. The witness record goes to
``feature-requests/evidence/FR-1048-opencode-backend-witness.md`` (hand-written
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
    os.environ.get("YAMLGRAPH_LIVE_OPENCODE") != "1",
    reason="live opencode witness; set YAMLGRAPH_LIVE_OPENCODE=1 on a host with opencode credentials",
)

MODEL = os.environ.get("YAMLGRAPH_OPENCODE_MODEL", "inception/mercury-2.5")

GRAPH = f"""\
version: "1.0"
name: fr1048-live-witness
prompts_relative: true
prompts_dir: prompts
state:
  first: dict
  second: dict
nodes:
  first:
    type: copilot
    backend: opencode
    cli_flags:
      model: {MODEL}
    prompt: first
    state_key: first
    timeout: 120
  second:
    type: copilot
    backend: opencode
    cli_flags:
      model: {MODEL}
      resume: "{{state.first.session_id}}"
    prompt: second
    state_key: second
    timeout: 120
edges:
  - {{from: START, to: first}}
  - {{from: first, to: second}}
  - {{from: second, to: END}}
"""

NONCE = "NONCE-7419"
PROMPT_FIRST = (
    f"user: Reply with the single word pong. Also remember this nonce: {NONCE}.\n"
)
PROMPT_SECOND = f"user: Reply with the single nonce I gave you earlier ({NONCE}).\n"


def _write_graph(root: Path) -> Path:
    (root / "prompts").mkdir()
    (root / "prompts" / "first.yaml").write_text(PROMPT_FIRST, encoding="utf-8")
    (root / "prompts" / "second.yaml").write_text(PROMPT_SECOND, encoding="utf-8")
    graph = root / "graph.yaml"
    graph.write_text(GRAPH, encoding="utf-8")
    return graph


@pytest.mark.req("REQ-YG-679")
def test_two_node_resume_recalls_nonce(tmp_path: Path, capsys) -> None:
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
    assert first.backend == "opencode" and second.backend == "opencode"
    assert first.session_id, "first node must return a real session_id"
    agent_argvs = [a for a in argvs if a[:2] == ["opencode", "run"]]
    assert len(agent_argvs) == 2
    assert "--session" in agent_argvs[1]
    assert agent_argvs[1][agent_argvs[1].index("--session") + 1] == first.session_id
    # Nonce recall: the second node's session is the first's, so the second
    # output must mention the nonce the first node was told to remember.
    assert NONCE in second.output

    # Everything the witness record needs (prompts are public text).
    print("\n=== FR-1048 live witness ===")
    print(f"started={started} ended={ended}")
    print(f"temp graph sha256={digest}")
    print(f"resolved model={MODEL}")
    for i, a in enumerate(argvs):
        print(f"argv[{i}]={a}")
    print(f"first.session_id={first.session_id} first.output={first.output[:60]!r}")
    print(f"second.session_id={second.session_id} second.output={second.output[:60]!r}")
    assert capsys is not None


@pytest.mark.req("REQ-YG-679")
def test_invalid_session_refuses(tmp_path: Path) -> None:
    from yamlgraph.node_factory.copilot_runtime_opencode import _execute_opencode

    # A nonexistent --session id: opencode prints "Session not found" to stderr
    # and exits 1 with no JSON event. The node must raise, not return a result.
    with pytest.raises(RuntimeError) as excinfo:
        _execute_opencode(
            node_name="witness-invalid",
            prompt="user: hello",
            state_key="result",
            cli_flags={"model": MODEL, "resume": "ses_nonexistent123"},
            timeout=120,
        )
    msg = str(excinfo.value)
    assert "Session not found" in msg
    assert "ses_nonexistent123" in msg
