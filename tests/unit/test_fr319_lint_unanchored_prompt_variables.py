"""FR-319 tests: lint warnings for unanchored prompt variables."""

from pathlib import Path

import pytest
import yaml

from yamlgraph.linter.graph_linter import lint_graph


def write_graph(tmp_path: Path, content: dict) -> Path:
    """Write graph YAML and return its path."""
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(content), encoding="utf-8")
    return graph_path


def write_prompt(tmp_path: Path, name: str, content: str) -> None:
    """Write a prompt YAML file in prompts/."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    (prompts_dir / f"{name}.yaml").write_text(content, encoding="utf-8")


@pytest.mark.req("REQ-YG-003")
def test_w023_emitted_for_unanchored_declared_variables(tmp_path: Path) -> None:
    """W023 should warn when node variables are never referenced in prompt text."""
    write_prompt(
        tmp_path,
        "judge",
        "system: Judge\nuser: Review topic {{ topic }}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr319-unanchored",
        "state": {"topic": "str", "fr_path": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "variables": {
                    "topic": "{state.topic}",
                    "fr_path": "{state.fr_path}",
                },
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }
    result = lint_graph(write_graph(tmp_path, graph), tmp_path)

    w023 = [issue for issue in result.issues if issue.code == "W023"]
    assert len(w023) == 1
    assert w023[0].severity == "warning"
    assert "judge" in w023[0].message
    assert "prompt 'judge'" in w023[0].message
    assert "fr_path" in w023[0].message
    assert "topic" not in w023[0].message


@pytest.mark.req("REQ-YG-003")
@pytest.mark.parametrize(
    "prompt_content",
    [
        "system: Judge\nuser: Review {fr_path}\n",
        "system: Judge\nuser: Review {{ fr_path }}\n",
    ],
)
def test_no_w023_when_declared_variables_are_referenced(
    tmp_path: Path, prompt_content: str
) -> None:
    """No W023 when declared variable is directly referenced."""
    write_prompt(tmp_path, "judge", prompt_content)
    graph = {
        "version": "1.0",
        "name": "fr319-anchored",
        "state": {"fr_path": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "variables": {"fr_path": "{state.fr_path}"},
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }
    result = lint_graph(write_graph(tmp_path, graph), tmp_path)
    assert not any(issue.code == "W023" for issue in result.issues)


@pytest.mark.req("REQ-YG-003")
def test_no_w023_for_state_qualified_jinja_reference(tmp_path: Path) -> None:
    """No W023 when prompt references variable via {{ state.key }}."""
    write_prompt(
        tmp_path,
        "judge",
        "system: Judge\nuser: Review {{ state.fr_path }}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr319-state-qualified",
        "state": {"fr_path": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "variables": {"fr_path": "{state.fr_path}"},
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }
    result = lint_graph(write_graph(tmp_path, graph), tmp_path)
    assert not any(issue.code == "W023" for issue in result.issues)


@pytest.mark.req("REQ-YG-003")
def test_nodes_without_prompt_or_variables_are_ignored(tmp_path: Path) -> None:
    """Nodes missing prompt or variables should not trigger W023."""
    write_prompt(tmp_path, "judge", "system: Judge\nuser: Ready\n")
    graph = {
        "version": "1.0",
        "name": "fr319-ignore",
        "nodes": {
            "python_node": {
                "type": "python",
                "module": "foo",
                "function": "bar",
                "variables": {"fr_path": "{state.fr_path}"},
                "state_key": "output",
            },
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "state_key": "verdict",
            },
        },
        "edges": [
            {"from": "START", "to": "python_node"},
            {"from": "python_node", "to": "judge"},
            {"from": "judge", "to": "END"},
        ],
    }
    result = lint_graph(write_graph(tmp_path, graph), tmp_path)
    assert not any(issue.code == "W023" for issue in result.issues)


@pytest.mark.req("REQ-YG-003")
def test_w023_is_warning_and_does_not_invalidate_lint_result(tmp_path: Path) -> None:
    """W023 should be warning severity and keep LintResult.valid true."""
    write_prompt(tmp_path, "judge", "system: Judge\nuser: No variable reference here\n")
    graph = {
        "version": "1.0",
        "name": "fr319-warning-only",
        "state": {"fr_path": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "variables": {"fr_path": "{state.fr_path}"},
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }
    result = lint_graph(write_graph(tmp_path, graph), tmp_path)

    w023 = [issue for issue in result.issues if issue.code == "W023"]
    assert len(w023) == 1
    assert w023[0].severity == "warning"
    assert result.valid is True
