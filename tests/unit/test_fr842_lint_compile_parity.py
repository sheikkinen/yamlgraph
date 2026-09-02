"""FR-842: lint must be a strict superset of compile-time validation.

A graph that lint passes must load through validate_config without error.
The live witness: GitClaw run 32361594593 failed at compile on a grouped
edge condition that `graph lint` had approved.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.linter import lint_graph

# The exact FR-840 grouped condition the loader rejects (GitClaw run 32361594593)
GROUPED_CONDITION = (
    "(review_verdict == 'REJECTED' or review_verdict == "
    "'APPROVED WITH REVISIONS') and _loop_counts.enforce == null"
)


def write_graph(tmp_path: Path, config: dict) -> Path:
    (tmp_path / "prompts").mkdir(exist_ok=True)
    (tmp_path / "prompts" / "test.yaml").write_text(
        "system: Test\nuser: Test {input}\n"
    , encoding="utf-8")
    graph_path = tmp_path / "test-graph.yaml"
    graph_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return graph_path


def valid_graph() -> dict:
    return {
        "version": "1.0",
        "name": "test",
        "description": "A test graph",
        "state": {"input": "str", "review_verdict": "str"},
        "nodes": {
            "step1": {"type": "llm", "prompt": "test", "state_key": "output"},
        },
        "edges": [
            {"from": "START", "to": "step1"},
            {"from": "step1", "to": "END"},
        ],
    }


def errors_of(result):
    return [issue for issue in result.issues if issue.severity == "error"]


@pytest.mark.req("REQ-YG-605")
def test_valid_graph_still_lints_clean(tmp_path):
    result = lint_graph(write_graph(tmp_path, valid_graph()), tmp_path)
    assert errors_of(result) == []
    assert result.valid is True


@pytest.mark.req("REQ-YG-605")
def test_grouped_condition_fails_lint_with_loader_message(tmp_path):
    config = valid_graph()
    config["edges"] = [
        {"from": "START", "to": "step1"},
        {"from": "step1", "to": "END", "condition": GROUPED_CONDITION},
        {"from": "step1", "to": "END"},
    ]
    result = lint_graph(write_graph(tmp_path, config), tmp_path)
    assert result.valid is False
    compile_errors = [
        issue
        for issue in errors_of(result)
        if issue.code == "E000" and "invalid condition syntax" in issue.message
    ]
    assert len(compile_errors) == 1


@pytest.mark.req("REQ-YG-605")
@pytest.mark.parametrize(
    "mutate",
    [
        lambda c: c["edges"].append({"to": "END"}),  # missing from
        lambda c: c["edges"].append({"from": "step1"}),  # missing to
        lambda c: c["nodes"]["step1"].update(
            {"type": "tool_call", "tool": "x", "on_error": "retry"}
        ),  # invalid on_error for tool_call
        lambda c: c.pop("nodes"),  # graph-schema violation
    ],
)
def test_loader_rejection_implies_lint_error(tmp_path, mutate):
    from yamlgraph.utils.validators import validate_config

    config = valid_graph()
    mutate(config)
    with pytest.raises((ValueError, KeyError)):
        validate_config(config)
    result = lint_graph(write_graph(tmp_path, config), tmp_path)
    assert result.valid is False
    assert any(issue.code == "E000" for issue in errors_of(result))


@pytest.mark.req("REQ-YG-605")
def test_existing_checks_still_run_alongside_compile_error(tmp_path):
    config = valid_graph()
    config["edges"][1]["condition"] = GROUPED_CONDITION
    config["edges"].append({"from": "step1", "to": "END"})
    config["nodes"]["step1"]["prompt"] = "missing-prompt-file"
    result = lint_graph(write_graph(tmp_path, config), tmp_path)
    codes = {issue.code for issue in result.issues}
    assert "E000" in codes
    assert len(codes) > 1  # unrelated findings are not hidden


@pytest.mark.req("REQ-YG-605")
def test_cli_exits_nonzero_via_normal_error_path(tmp_path, capsys):
    import argparse

    from yamlgraph.cli.graph_validate import cmd_graph_lint

    config = valid_graph()
    config["edges"][1]["condition"] = GROUPED_CONDITION
    config["edges"].append({"from": "step1", "to": "END"})
    graph_path = write_graph(tmp_path, config)
    args = argparse.Namespace(graph_path=[str(graph_path)], json=False)
    with pytest.raises(SystemExit) as excinfo:
        cmd_graph_lint(args)
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "invalid condition syntax" in out


@pytest.mark.req("REQ-YG-605")
def test_json_mode_reports_compile_error_as_normal_issue(tmp_path, capsys):
    import argparse
    import json as jsonlib

    from yamlgraph.cli.graph_validate import cmd_graph_lint

    config = valid_graph()
    config["edges"][1]["condition"] = GROUPED_CONDITION
    config["edges"].append({"from": "step1", "to": "END"})
    graph_path = write_graph(tmp_path, config)
    args = argparse.Namespace(graph_path=[str(graph_path)], json=True)
    with pytest.raises(SystemExit) as excinfo:
        cmd_graph_lint(args)
    assert excinfo.value.code == 1
    payload = jsonlib.loads(capsys.readouterr().out.strip())
    assert payload["valid"] is False
    assert any(
        issue["code"] == "E000" and "invalid condition syntax" in issue["message"]
        for issue in payload["issues"]
    )
