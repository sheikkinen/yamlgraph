"""Integration test: copilot session ID propagation between chained nodes.

FR-274: Validates that session_id flows from node 1 to node 2's --resume flag
when two copilot nodes are chained in a compiled graph.

Hypothesis: With the current stderr-based extraction (regex Session:\\s*...),
session_id is always None because copilot CLI never emits that format.
Node 2 therefore never receives --resume, starting a fresh session.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.graph_loader import compile_graph, load_graph_config

SUBPROCESS_RUN = "yamlgraph.node_factory.copilot_node.subprocess.run"


def _copilot_calls(mock_run):
    """Filter mock calls to only those with a 'copilot' command (first arg)."""
    return [
        c
        for c in mock_run.call_args_list
        if c[0] and isinstance(c[0][0], list) and c[0][0][0] == "copilot"
    ]


GRAPH_YAML = """\
version: "1.0"
name: session-propagation-test
description: Two copilot nodes chained with session resume

prompts_relative: true
prompts_dir: prompts

state:
  task: str
  phase1_result: dict
  phase2_result: dict

nodes:
  phase1:
    type: copilot
    prompt: phase1
    state_key: phase1_result
    timeout: 10
    variables:
      task: "{state.task}"

  phase2:
    type: copilot
    prompt: phase2
    cli_flags:
      resume: "{state.phase1_result.session_id}"
    state_key: phase2_result
    timeout: 10
    variables:
      task: "{state.task}"

edges:
  - from: START
    to: phase1
  - from: phase1
    to: phase2
  - from: phase2
    to: END
"""


def _write_graph(tmp_path: Path) -> Path:
    """Write the two-node graph and its prompt files to tmp_path."""
    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text(GRAPH_YAML)

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "phase1.yaml").write_text(
        "system: You are a helper.\nuser: Do phase 1 for {task}"
    )
    (prompts_dir / "phase2.yaml").write_text(
        "system: You are a helper.\nuser: Do phase 2 for {task}"
    )
    return graph_file


@pytest.mark.req("REQ-YG-105")
class TestCopilotSessionPropagation:
    """Integration: session_id flows from phase1 to phase2 --resume."""

    def test_session_id_none_with_empty_stderr(self, tmp_path: Path) -> None:
        """BUG PROOF: empty stderr (realistic) → session_id=None → no --resume.

        This is the current broken behavior. Copilot CLI with --silent
        produces empty stderr, so _extract_session_id returns None.
        Phase2 resolves {state.phase1_result.session_id} to None,
        and --resume is never passed.
        """
        graph_file = _write_graph(tmp_path)
        config = load_graph_config(graph_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        mock_result = MagicMock()
        mock_result.stdout = "phase output"
        mock_result.stderr = ""  # Realistic: --silent produces empty stderr
        mock_result.returncode = 0

        with patch(SUBPROCESS_RUN, return_value=mock_result) as mock_run:
            result = compiled.invoke({"task": "test"})

        # Phase1 ran
        assert result["phase1_result"] is not None
        assert result["phase1_result"].session_id is None  # BUG: always None

        # Phase2 ran but without --resume
        assert result["phase2_result"] is not None
        copilot_cmds = _copilot_calls(mock_run)
        assert len(copilot_cmds) == 2

        # Inspect phase2's subprocess call — --resume should be ABSENT
        phase2_cmd = copilot_cmds[1][0][0]
        assert "--resume" not in phase2_cmd, (
            "Expected --resume to be absent when session_id is None, "
            f"but found it in: {phase2_cmd}"
        )

    def test_session_id_propagates_when_extracted(self, tmp_path: Path) -> None:
        """FIX PROOF: when session_id is extracted, phase2 gets --resume <uuid>.

        Simulates a working extraction (e.g., after FR-274 fix with --share).
        Phase1 returns a valid session_id, phase2 passes --resume <uuid>.
        """
        graph_file = _write_graph(tmp_path)
        config = load_graph_config(graph_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        session_uuid = "d0137402-936d-4e5c-a3fe-27e924ef5dd2"

        call_count = 0

        def mock_subprocess_run(cmd, **kwargs):
            nonlocal call_count
            # Only count actual copilot CLI invocations
            if not (isinstance(cmd, list) and cmd[0] == "copilot"):
                return MagicMock(stdout="", stderr="", returncode=0)
            call_count += 1
            result = MagicMock()
            result.stdout = f"phase {call_count} output"
            result.returncode = 0
            result.stderr = ""
            if call_count == 1 and "--share" in cmd:
                # FR-274: Write share file with session ID
                share_idx = cmd.index("--share") + 1
                share_path = Path(cmd[share_idx])
                share_path.parent.mkdir(parents=True, exist_ok=True)
                share_path.write_text(
                    f"# Session\n> - **Session ID:** `{session_uuid}`\n"
                )
            return result

        with patch(SUBPROCESS_RUN, side_effect=mock_subprocess_run) as mock_run:
            result = compiled.invoke({"task": "test"})

        # Phase1 extracted session_id
        copilot_cmds = _copilot_calls(mock_run)
        assert len(copilot_cmds) == 2
        assert result["phase1_result"].session_id == session_uuid

        # Phase2 received --resume with the correct UUID
        phase2_cmd = copilot_cmds[1][0][0]
        assert "--resume" in phase2_cmd, (
            f"Expected --resume in phase2 command, got: {phase2_cmd}"
        )
        resume_idx = phase2_cmd.index("--resume")
        assert phase2_cmd[resume_idx + 1] == session_uuid

    def test_session_id_none_with_ansi_stats_stderr(self, tmp_path: Path) -> None:
        """BUG PROOF: ANSI stats in stderr (non-silent) → session_id=None.

        Without --silent, copilot CLI emits ANSI-formatted stats to stderr
        (Changes, Requests, Tokens). No session ID is present.
        """
        graph_file = _write_graph(tmp_path)
        config = load_graph_config(graph_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        # Realistic non-silent stderr output (ANSI stripped for readability)
        ansi_stderr = "Changes: 3 files | Requests: 12 | Tokens: 4,521 in / 2,103 out"

        mock_result = MagicMock()
        mock_result.stdout = "phase output"
        mock_result.stderr = ansi_stderr
        mock_result.returncode = 0

        with patch(SUBPROCESS_RUN, return_value=mock_result) as mock_run:
            result = compiled.invoke({"task": "test"})

        # Session ID not found in ANSI stats
        assert result["phase1_result"].session_id is None

        # Phase2 invoked without --resume
        copilot_cmds = _copilot_calls(mock_run)
        phase2_cmd = copilot_cmds[1][0][0]
        assert "--resume" not in phase2_cmd


# =============================================================================
# CopilotResult.output → Python unwrap node integration
# =============================================================================

UNWRAP_TOOL_CODE = '''\
"""Minimal unwrap tool for integration testing."""

import json

from yamlgraph.models.schemas import CopilotResult


def unwrap_analysis(state: dict) -> dict:
    """Parse CopilotResult.output JSON into a validated dict.

    Mirrors the philosopher unwrap pattern: copilot node stores
    CopilotResult in state_key, python node reads it and parses .output.
    """
    raw = state.get("analysis_result")
    if not isinstance(raw, CopilotResult):
        raise ValueError(f"Expected CopilotResult, got {type(raw).__name__}")

    parsed = json.loads(raw.output)
    return {"analysis_parsed": parsed}
'''

UNWRAP_GRAPH_YAML = """\
version: "1.0"
name: copilot-unwrap-test
description: Copilot node → Python unwrap node

prompts_relative: true
prompts_dir: prompts

state:
  topic: str
  analysis_result: dict
  analysis_parsed: dict

tools:
  unwrap_tool:
    type: python
    path: {tool_path}
    function: unwrap_analysis

nodes:
  analyze:
    type: copilot
    prompt: analyze
    state_key: analysis_result
    timeout: 10
    variables:
      topic: "{state.topic}"

  unwrap:
    type: python
    tool: unwrap_tool
    state_key: analysis_parsed

edges:
  - from: START
    to: analyze
  - from: analyze
    to: unwrap
  - from: unwrap
    to: END
"""


def _write_unwrap_graph(tmp_path: Path) -> Path:
    """Write copilot→unwrap graph with tool Python file."""
    tool_file = tmp_path / "tools.py"
    tool_file.write_text(UNWRAP_TOOL_CODE)

    graph_yaml = UNWRAP_GRAPH_YAML.replace("{tool_path}", str(tool_file))
    graph_file = tmp_path / "graph.yaml"
    graph_file.write_text(graph_yaml)

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "analyze.yaml").write_text(
        "system: You are an analyst.\nuser: Analyze {topic}"
    )
    return graph_file


@pytest.mark.req("REQ-YG-105")
class TestCopilotOutputUnwrap:
    """Integration: CopilotResult.output flows to Python unwrap node."""

    def test_copilot_output_parsed_by_python_node(self, tmp_path: Path) -> None:
        """Copilot stdout → CopilotResult.output → python node parses JSON."""
        graph_file = _write_unwrap_graph(tmp_path)
        config = load_graph_config(graph_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        copilot_json_output = '{"summary": "AI is transformative", "score": 0.95}'

        mock_result = MagicMock()
        mock_result.stdout = copilot_json_output
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch(SUBPROCESS_RUN, return_value=mock_result):
            result = compiled.invoke({"topic": "AI"})

        # CopilotResult stored in state
        assert result["analysis_result"].output == copilot_json_output
        assert result["analysis_result"].backend == "cli"

        # Python unwrap node parsed the JSON
        assert result["analysis_parsed"] == {
            "summary": "AI is transformative",
            "score": 0.95,
        }

    def test_copilot_output_with_session_id_and_unwrap(self, tmp_path: Path) -> None:
        """Session ID extracted AND output parsed in same pipeline.

        Proves both CopilotResult.session_id and CopilotResult.output
        are independently usable by downstream nodes.
        """
        graph_file = _write_unwrap_graph(tmp_path)
        config = load_graph_config(graph_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        session_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        copilot_json_output = '{"key": "value"}'

        def mock_subprocess_run(cmd, **kwargs):
            result = MagicMock()
            result.stdout = copilot_json_output
            result.stderr = ""
            result.returncode = 0
            # FR-274: Write share file with session ID
            if "--share" in cmd:
                share_idx = cmd.index("--share") + 1
                share_path = Path(cmd[share_idx])
                share_path.parent.mkdir(parents=True, exist_ok=True)
                share_path.write_text(
                    f"# Session\n> - **Session ID:** `{session_uuid}`\n"
                )
            return result

        with patch(SUBPROCESS_RUN, side_effect=mock_subprocess_run):
            result = compiled.invoke({"topic": "test"})

        # Both session_id and output are preserved
        assert result["analysis_result"].session_id == session_uuid
        assert result["analysis_result"].output == copilot_json_output
        assert result["analysis_parsed"] == {"key": "value"}

    def test_copilot_non_json_output_raises_in_unwrap(self, tmp_path: Path) -> None:
        """Non-JSON copilot output → unwrap raises ValueError (Commandment 6)."""
        graph_file = _write_unwrap_graph(tmp_path)
        config = load_graph_config(graph_file)
        graph = compile_graph(config)
        compiled = graph.compile()

        mock_result = MagicMock()
        mock_result.stdout = "This is plain text, not JSON"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with (
            patch(SUBPROCESS_RUN, return_value=mock_result),
            pytest.raises(Exception, match="Expecting value|JSON"),
        ):
            compiled.invoke({"topic": "test"})
