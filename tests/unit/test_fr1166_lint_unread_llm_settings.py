"""FR-1166: lint LLM settings written where yamlgraph never reads them.

W072 — a tuning key in graph ``metadata:`` or a referenced prompt's
``metadata:``. W073 — any key but provider/model on a race candidate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
import yaml

from yamlgraph.linter.graph_linter import lint_graph

SETTINGS = ["thinking_budget", "temperature", "max_tokens", "effort"]
CANDIDATE_A = {"provider": "vertex", "model": "gemini-2.5-flash"}
CANDIDATE_B = {"provider": "azure", "model": "gpt-5.4-mini"}


def _write(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _prompt(metadata: dict | None = None, **top: object) -> dict:
    data: dict = {
        "system": "You classify.",
        "user": "{{ text }}",
        "schema": {"name": "Pick", "fields": {"intent": {"type": "str"}}},
        **top,
    }
    if metadata is not None:
        data["metadata"] = metadata
    return data


def _llm_graph(**extra: object) -> dict:
    return {
        "name": "fr1166",
        "state": {"text": "str", "answer": "str"},
        "nodes": {"ask": {"type": "llm", "prompt": "ask", "state_key": "answer"}},
        "edges": [{"from": "START", "to": "ask"}, {"from": "ask", "to": "END"}],
        **extra,
    }


def _race_graph(candidates: list[dict]) -> dict:
    return {
        "name": "fr1166_race",
        "state": {"text": "str", "answer": "str"},
        "nodes": {
            "fast": {
                "type": "race",
                "prompt": "ask",
                "state_key": "answer",
                "candidates": candidates,
            }
        },
        "edges": [{"from": "START", "to": "fast"}, {"from": "fast", "to": "END"}],
    }


def _router_race_graph(candidates: list[dict]) -> dict:
    return {
        "name": "fr1166_router_race",
        "state": {"text": "str", "answer": "str"},
        "nodes": {
            "classify": {
                "type": "router",
                "prompt": "ask",
                "route_field": "intent",
                "routes": {"a": "left", "b": "right"},
                "default_route": "left",
                "candidates": candidates,
            },
            "left": {"type": "llm", "prompt": "ask", "state_key": "answer"},
            "right": {"type": "llm", "prompt": "ask", "state_key": "answer"},
        },
        "edges": [
            {"from": "START", "to": "classify"},
            {"from": "classify", "to": ["left", "right"], "type": "conditional"},
            {"from": "left", "to": "END"},
            {"from": "right", "to": "END"},
        ],
    }


def _codes(result, code: str) -> list:
    return [issue for issue in result.issues if issue.code == code]


def _lint(tmp_path: Path, graph: dict, prompt: dict | None = None):
    _write(tmp_path / "prompts" / "ask.yaml", prompt or _prompt())
    graph_path = _write(tmp_path / "graph.yaml", graph)
    return lint_graph(graph_path, tmp_path)


# --- AC-01: graph metadata ----------------------------------------------------


@pytest.mark.req("REQ-YG-730")
@pytest.mark.parametrize("key", SETTINGS)
@pytest.mark.parametrize("value", [0, None])
def test_w072_graph_metadata_setting(tmp_path: Path, key: str, value: object) -> None:
    result = _lint(tmp_path, _llm_graph(metadata={"owner": "csap", key: value}))

    issues = _codes(result, "W072")
    assert len(issues) == 1
    issue = issues[0]
    assert issue.severity == "warning"
    assert "graph metadata" in issue.message
    assert f"'{key}'" in issue.message
    assert f"defaults.{key}" in issue.fix
    assert result.valid is True


@pytest.mark.req("REQ-YG-730")
@pytest.mark.parametrize("key", ["max_tokens", "effort"])
def test_w072_unforwarded_setting_does_not_promise_race(
    tmp_path: Path, key: str
) -> None:
    result = _lint(tmp_path, _llm_graph(metadata={key: 1}))

    fix = _codes(result, "W072")[0].fix
    assert "race" in fix
    assert "not" in fix


# --- AC-02: referenced prompt metadata ----------------------------------------


@pytest.mark.req("REQ-YG-730")
@pytest.mark.parametrize("key", SETTINGS)
def test_w072_prompt_metadata_project_root(tmp_path: Path, key: str) -> None:
    result = _lint(tmp_path, _llm_graph(), _prompt(metadata={key: 0}))

    issues = _codes(result, "W072")
    assert len(issues) == 1
    assert "prompt 'ask'" in issues[0].message
    assert f"'{key}'" in issues[0].message
    assert f"defaults.{key}" in issues[0].fix


@pytest.mark.req("REQ-YG-730")
def test_w072_prompt_metadata_graph_relative(tmp_path: Path) -> None:
    graph_dir = tmp_path / "graphs" / "nav"
    _write(graph_dir / "p" / "ask.yaml", _prompt(metadata={"thinking_budget": 0}))
    graph_path = _write(
        graph_dir / "graph.yaml",
        _llm_graph(defaults={"prompts_relative": True, "prompts_dir": "p"}),
    )

    issues = _codes(lint_graph(graph_path, tmp_path), "W072")
    assert len(issues) == 1
    assert "prompt 'ask'" in issues[0].message


@pytest.mark.req("REQ-YG-730")
def test_w072_prompt_reported_once_when_shared(tmp_path: Path) -> None:
    result = _lint(
        tmp_path,
        _router_race_graph([CANDIDATE_A, CANDIDATE_B]),
        _prompt(metadata={"thinking_budget": 0}),
    )

    assert len(_codes(result, "W072")) == 1


# --- AC-03: negatives -----------------------------------------------------------


@pytest.mark.req("REQ-YG-730")
def test_no_w072_for_non_setting_metadata_and_top_level_prompt_keys(
    tmp_path: Path,
) -> None:
    result = _lint(
        tmp_path,
        _llm_graph(metadata={"owner": "x", "description": "y", "version": 2}),
        _prompt(metadata={"author": "z"}, provider="vertex", model="gemini-2.5"),
    )

    assert _codes(result, "W072") == []
    assert _codes(result, "W073") == []


@pytest.mark.req("REQ-YG-730")
def test_no_w072_for_missing_prompt(tmp_path: Path) -> None:
    graph_path = _write(tmp_path / "graph.yaml", _llm_graph())

    result = lint_graph(graph_path, tmp_path)

    assert _codes(result, "W072") == []
    assert any(issue.code == "E004" for issue in result.issues)


# --- AC-04 / AC-05: race candidates ---------------------------------------------


RACE_SHAPES = [
    pytest.param(_race_graph, "fast", id="race"),
    pytest.param(_router_race_graph, "classify", id="router_race"),
]


@pytest.mark.req("REQ-YG-730")
@pytest.mark.parametrize(("build", "node"), RACE_SHAPES)
@pytest.mark.parametrize("key", ["temperature", "thinking_budget"])
def test_w073_forwarded_setting_on_candidate(
    tmp_path: Path, build, node: str, key: str
) -> None:
    result = _lint(tmp_path, build([CANDIDATE_A, {**CANDIDATE_B, key: 0}]))

    issues = _codes(result, "W073")
    assert len(issues) == 1
    issue = issues[0]
    assert issue.severity == "warning"
    assert f"'{node}'" in issue.message
    assert "candidate 1" in issue.message
    assert f"'{key}'" in issue.message
    assert "defaults" in issue.fix
    assert result.valid is True


@pytest.mark.req("REQ-YG-730")
@pytest.mark.parametrize(("build", "node"), RACE_SHAPES)
@pytest.mark.parametrize("key", ["max_tokens", "effort"])
def test_w073_unforwarded_setting_on_candidate(
    tmp_path: Path, build, node: str, key: str
) -> None:
    result = _lint(tmp_path, build([{**CANDIDATE_A, key: 5}, CANDIDATE_B]))

    issue = _codes(result, "W073")[0]
    assert "candidate 0" in issue.message
    assert "does not apply" in issue.fix
    assert "remove" in issue.fix.lower()
    assert "defaults" not in issue.fix


@pytest.mark.req("REQ-YG-730")
@pytest.mark.parametrize(("build", "node"), RACE_SHAPES)
def test_w073_arbitrary_key_and_one_issue_per_key(
    tmp_path: Path, build, node: str
) -> None:
    candidate = {**CANDIDATE_B, "weight": 2, "thinking_budget": 0}
    result = _lint(tmp_path, build([CANDIDATE_A, candidate]))

    issues = _codes(result, "W073")
    assert len(issues) == 2
    weight = next(i for i in issues if "'weight'" in i.message)
    assert "provider" in weight.fix and "model" in weight.fix


@pytest.mark.req("REQ-YG-730")
@pytest.mark.parametrize(("build", "node"), RACE_SHAPES)
@pytest.mark.parametrize(
    "candidates",
    [
        [{"provider": "vertex"}, {"provider": "azure"}],
        [{"model": "gemini-2.5-flash"}, {"model": "gpt-5.4-mini"}],
        [CANDIDATE_A, CANDIDATE_B],
    ],
    ids=["provider_only", "model_only", "provider_model"],
)
def test_no_w073_for_clean_candidates(
    tmp_path: Path, build, node: str, candidates: list[dict]
) -> None:
    assert _codes(_lint(tmp_path, build(candidates)), "W073") == []


# --- AC-01: CLI registration ----------------------------------------------------


@pytest.mark.req("REQ-YG-730")
def test_cli_graph_lint_reports_w072_and_w073(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from yamlgraph.cli.graph_validate import cmd_graph_lint

    graph = _race_graph([CANDIDATE_A, {**CANDIDATE_B, "thinking_budget": 0}])
    graph["metadata"] = {"thinking_budget": 0}
    _write(tmp_path / "prompts" / "ask.yaml", _prompt())
    graph_path = _write(tmp_path / "graph.yaml", graph)

    cmd_graph_lint(argparse.Namespace(graph_path=[str(graph_path)], json=True))

    codes = {i["code"] for i in json.loads(capsys.readouterr().out)["issues"]}
    assert {"W072", "W073"} <= codes
