"""Acceptance tests for FR-363: per-node OTel scoping in copilot node."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _write_prompt(tmp_path: Path) -> Path:
    prompt_file = tmp_path / "prompts" / "test.yaml"
    prompt_file.parent.mkdir(parents=True)
    prompt_file.write_text("system: Test\nuser: Hello", encoding="utf-8")
    return prompt_file


@pytest.mark.req("REQ-YG-087")
def test_ac01_execute_cli_sets_node_scoped_otel_export_path_when_yamlgraph_otel_dir_is_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-01: subprocess env includes node-scoped exporter path when enabled."""
    from yamlgraph.node_factory.copilot_node import create_copilot_node

    prompt_file = _write_prompt(tmp_path)
    otel_dir = tmp_path / "otel"
    monkeypatch.setenv("YAMLGRAPH_OTEL_DIR", str(otel_dir))

    config = {"type": "copilot", "prompt": str(prompt_file), "state_key": "result"}
    mock_result = MagicMock(stdout="Response", stderr="", returncode=0)

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        node_fn = create_copilot_node("plan", config)
        node_fn({})

    env = mock_run.call_args.kwargs.get("env")
    assert env is not None
    assert env["COPILOT_OTEL_FILE_EXPORTER_PATH"] == str(otel_dir / "plan.otel.jsonl")


@pytest.mark.req("REQ-YG-087")
def test_ac02_execute_cli_preserves_behavior_when_yamlgraph_otel_dir_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-02: no forced exporter override when YAMLGRAPH_OTEL_DIR is unset."""
    from yamlgraph.node_factory.copilot_node import create_copilot_node

    prompt_file = _write_prompt(tmp_path)
    monkeypatch.delenv("YAMLGRAPH_OTEL_DIR", raising=False)

    config = {"type": "copilot", "prompt": str(prompt_file), "state_key": "result"}
    mock_result = MagicMock(stdout="Response", stderr="", returncode=0)

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        node_fn = create_copilot_node("plan", config)
        node_fn({})

    env = mock_run.call_args.kwargs.get("env")
    assert env is None or "COPILOT_OTEL_FILE_EXPORTER_PATH" not in env


@pytest.mark.req("REQ-YG-087")
def test_ac03_two_copilot_nodes_receive_distinct_export_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-03: node names produce different exporter files."""
    from yamlgraph.node_factory.copilot_node import create_copilot_node

    prompt_file = _write_prompt(tmp_path)
    otel_dir = tmp_path / "otel"
    monkeypatch.setenv("YAMLGRAPH_OTEL_DIR", str(otel_dir))

    config = {"type": "copilot", "prompt": str(prompt_file), "state_key": "result"}
    mock_result = MagicMock(stdout="Response", stderr="", returncode=0)
    exporter_paths: list[str] = []

    def capture_run(*args, **kwargs):
        env = kwargs.get("env")
        exporter_paths.append(env["COPILOT_OTEL_FILE_EXPORTER_PATH"])
        return mock_result

    with patch("subprocess.run", side_effect=capture_run):
        create_copilot_node("plan", config)({})
        create_copilot_node("judge", config)({})

    assert exporter_paths == [
        str(otel_dir / "plan.otel.jsonl"),
        str(otel_dir / "judge.otel.jsonl"),
    ]
    assert exporter_paths[0] != exporter_paths[1]


@pytest.mark.req("REQ-YG-105")
def test_ac04_session_id_extraction_contract_unchanged_with_otel_dir_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-04: --share extraction still populates CopilotResult.session_id."""
    from yamlgraph.node_factory.copilot_node import create_copilot_node

    prompt_file = _write_prompt(tmp_path)
    otel_dir = tmp_path / "otel"
    monkeypatch.setenv("YAMLGRAPH_OTEL_DIR", str(otel_dir))

    config = {"type": "copilot", "prompt": str(prompt_file), "state_key": "result"}
    mock_result = MagicMock(stdout="Response", stderr="", returncode=0)
    share_content = (
        "# Session\n\n"
        "> [!NOTE]\n"
        "> - **Session ID:** `d0137402-936d-4e5c-a3fe-27e924ef5dd2`\n"
    )

    def mock_subprocess_run(cmd, **kwargs):
        if "--share" in cmd:
            share_idx = cmd.index("--share") + 1
            share_path = Path(cmd[share_idx])
            share_path.parent.mkdir(parents=True, exist_ok=True)
            share_path.write_text(share_content, encoding="utf-8")
        return mock_result

    with patch("subprocess.run", side_effect=mock_subprocess_run):
        node_fn = create_copilot_node("implement", config)
        result = node_fn({})

    assert result["result"].session_id == "d0137402-936d-4e5c-a3fe-27e924ef5dd2"
