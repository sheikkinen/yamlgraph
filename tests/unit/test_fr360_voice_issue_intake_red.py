"""Acceptance tests for FR-360 voice-driven GitHub issue intake."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

import projects.incaller.nodes.create_issue as create_issue_node

REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = REPO_ROOT / "projects" / "incaller" / "graph.yaml"
README_PATH = REPO_ROOT / "projects" / "incaller" / "README.md"


def _load_graph() -> dict:
    with GRAPH_PATH.open() as f:
        loaded = yaml.safe_load(f)
    assert isinstance(loaded, dict)
    return loaded


def _has_edge(graph: dict, src: str, dst: str, condition: str | None = None) -> bool:
    for edge in graph["edges"]:
        if edge.get("from") != src or edge.get("to") != dst:
            continue
        if condition is None or edge.get("condition") == condition:
            return True
    return False


@pytest.mark.req("REQ-YG-333")
def test_ac01_graph_declares_issue_intake_state_keys() -> None:
    graph = _load_graph()
    state = graph["state"]
    assert "mode" in state
    assert "issue_url" in state
    assert "issue_number" in state
    assert "issue_create_error" in state


@pytest.mark.req("REQ-YG-334")
def test_ac02_confirmed_recap_routes_to_create_issue_only_in_issue_mode() -> None:
    graph = _load_graph()

    assert _has_edge(
        graph,
        "analyze_recap_response",
        "create_issue",
        'recap_analysis.is_confirmed == True and mode == "github_issue_intake"',
    )
    assert _has_edge(
        graph,
        "analyze_recap_response",
        "generate_goodbye",
        'recap_analysis.is_confirmed == True and mode != "github_issue_intake"',
    )
    assert _has_edge(
        graph,
        "analyze_recap_response",
        "generate_goodbye",
        'recap_count >= 3 and mode == "github_issue_intake"',
    )
    assert not _has_edge(
        graph,
        "analyze_recap_response",
        "create_issue",
        'recap_count >= 3 and mode == "github_issue_intake"',
    )


@pytest.mark.req("REQ-YG-335")
def test_ac03_create_issue_executes_gh_and_returns_issue_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def _fake_run(
        command: list[str], *, capture_output: bool, text: bool, check: bool
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        assert capture_output is True
        assert text is True
        assert check is True
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="https://github.com/sheikkinen/yamlgraph/issues/42\n",
            stderr="",
        )

    monkeypatch.setattr(create_issue_node.subprocess, "run", _fake_run)
    result = create_issue_node.create_issue(
        {
            "extracted": {
                "issue_title": "FR-360 acceptance",
                "issue_type": "feat",
                "issue_summary": "Caller described a new intake flow",
                "chaplain_opt_in": "no",
            }
        }
    )

    assert len(calls) == 1
    assert calls[0][0:3] == ["gh", "issue", "create"]
    assert "--title" in calls[0]
    assert "--body" in calls[0]
    assert result["issue_url"] == "https://github.com/sheikkinen/yamlgraph/issues/42"
    assert result["issue_number"] == 42
    assert result["issue_create_error"] is None


@pytest.mark.req("REQ-YG-336")
@pytest.mark.parametrize(
    ("chaplain_opt_in", "expect_label"),
    [
        ("yes", True),
        ("  YES  ", True),
        (True, True),
        ("no", False),
        (False, False),
    ],
)
def test_ac04_chaplain_label_applied_only_when_opted_in(
    monkeypatch: pytest.MonkeyPatch,
    chaplain_opt_in: str | bool,
    expect_label: bool,
) -> None:
    calls: list[list[str]] = []

    def _fake_run(
        command: list[str], *, capture_output: bool, text: bool, check: bool
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="https://github.com/sheikkinen/yamlgraph/issues/91\n",
            stderr="",
        )

    monkeypatch.setattr(create_issue_node.subprocess, "run", _fake_run)
    result = create_issue_node.create_issue(
        {
            "extracted": {
                "issue_title": "Label behavior",
                "issue_type": "docs",
                "issue_summary": "Validate chaplain label opt-in behavior",
                "chaplain_opt_in": chaplain_opt_in,
            }
        }
    )

    assert len(calls) == 1
    has_label = "--label" in calls[0] and "chaplain" in calls[0]
    assert has_label is expect_label
    assert result["issue_create_error"] is None


@pytest.mark.req("REQ-YG-337")
def test_ac05_create_issue_failure_sets_explicit_error_without_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _missing_gh(
        _command: list[str], *, capture_output: bool, text: bool, check: bool
    ) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("gh")

    monkeypatch.setattr(create_issue_node.subprocess, "run", _missing_gh)
    missing_result = create_issue_node.create_issue(
        {
            "extracted": {
                "issue_title": "Missing gh",
                "issue_type": "fix",
                "issue_summary": "Simulate gh missing",
                "chaplain_opt_in": "no",
            }
        }
    )
    assert missing_result["issue_url"] is None
    assert missing_result["issue_number"] is None
    assert "gh" in missing_result["issue_create_error"]

    def _failed_gh(
        command: list[str], *, capture_output: bool, text: bool, check: bool
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            returncode=4,
            cmd=command,
            output="",
            stderr="authentication failed",
        )

    monkeypatch.setattr(create_issue_node.subprocess, "run", _failed_gh)
    failed_result = create_issue_node.create_issue(
        {
            "extracted": {
                "issue_title": "Auth fail",
                "issue_type": "feat",
                "issue_summary": "Simulate gh auth failure",
                "chaplain_opt_in": "yes",
            }
        }
    )
    assert failed_result["issue_url"] is None
    assert failed_result["issue_number"] is None
    assert "authentication failed" in failed_result["issue_create_error"]


@pytest.mark.req("REQ-YG-338")
def test_ac06_issue_url_or_error_readback_nodes_route_to_goodbye() -> None:
    graph = _load_graph()
    nodes = graph["nodes"]
    assert nodes["speak_issue_url"]["type"] == "llm"
    assert nodes["speak_issue_url"]["state_key"] == "next_utterance"
    assert nodes["speak_issue_error"]["type"] == "llm"
    assert nodes["speak_issue_error"]["state_key"] == "next_utterance"

    assert _has_edge(graph, "create_issue", "speak_issue_url", "issue_url != None")
    assert _has_edge(
        graph, "create_issue", "speak_issue_error", "issue_create_error != None"
    )
    assert _has_edge(graph, "speak_issue_url", "speak")
    assert _has_edge(graph, "speak_issue_error", "speak")


@pytest.mark.req("REQ-YG-339")
def test_ac07_readme_documents_github_issue_intake_mode() -> None:
    readme = README_PATH.read_text()
    assert "github_issue_intake" in readme
    assert "gh auth login" in readme
