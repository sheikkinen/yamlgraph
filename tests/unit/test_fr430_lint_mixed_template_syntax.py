"""FR-430 tests: lint warning for mixed simple and Jinja2 template syntax."""

from pathlib import Path

import pytest
import yaml

from yamlgraph.linter.graph_linter import lint_graph


def write_graph(tmp_path: Path, content: dict) -> Path:
    """Write graph YAML and return its path."""
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(content))
    return graph_path


def write_prompt(tmp_path: Path, name: str, content: str) -> None:
    """Write a prompt YAML file in prompts/."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    (prompts_dir / f"{name}.yaml").write_text(content)


@pytest.mark.req("REQ-YG-003")
def test_w024_emitted_for_mixed_simple_and_jinja_syntax(tmp_path: Path) -> None:
    """W024 should warn when simple {var} and Jinja2 syntax coexist."""
    write_prompt(
        tmp_path,
        "judge",
        "system: Judge\nuser: File {fr_path}; reviewer {{ reviewer }}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr430-mixed",
        "state": {"fr_path": "str", "reviewer": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }

    result = lint_graph(write_graph(tmp_path, graph), tmp_path)
    w024 = [issue for issue in result.issues if issue.code == "W024"]

    assert len(w024) == 1
    assert w024[0].severity == "warning"
    assert "mixes simple {var} and Jinja2" in w024[0].message
    assert "Convert simple placeholders" in (w024[0].fix or "")


@pytest.mark.req("REQ-YG-003")
def test_no_w024_for_pure_simple_syntax(tmp_path: Path) -> None:
    """Pure simple placeholders should not trigger W024."""
    write_prompt(
        tmp_path,
        "judge",
        "system: Judge\nuser: File {fr_path}; topic {topic}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr430-simple-only",
        "state": {"fr_path": "str", "topic": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }

    result = lint_graph(write_graph(tmp_path, graph), tmp_path)
    assert not any(issue.code == "W024" for issue in result.issues)


@pytest.mark.req("REQ-YG-003")
def test_no_w024_for_pure_jinja_syntax(tmp_path: Path) -> None:
    """Pure Jinja2 templates should not trigger W024."""
    write_prompt(
        tmp_path,
        "judge",
        "system: Judge\nuser: File {{ fr_path }}; {% if topic %}Topic {{ topic }}{% endif %}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr430-jinja-only",
        "state": {"fr_path": "str", "topic": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "judge",
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }

    result = lint_graph(write_graph(tmp_path, graph), tmp_path)
    assert not any(issue.code == "W024" for issue in result.issues)


@pytest.mark.req("REQ-YG-003")
def test_no_w024_when_prompt_file_missing(tmp_path: Path) -> None:
    """Missing prompt files should not produce W024 (E004 handles missing files)."""
    graph = {
        "version": "1.0",
        "name": "fr430-missing-prompt",
        "state": {"fr_path": "str"},
        "nodes": {
            "judge": {
                "type": "llm",
                "prompt": "missing_prompt",
                "state_key": "verdict",
            }
        },
        "edges": [{"from": "START", "to": "judge"}, {"from": "judge", "to": "END"}],
    }

    result = lint_graph(write_graph(tmp_path, graph), tmp_path)
    assert not any(issue.code == "W024" for issue in result.issues)
    assert any(issue.code == "E004" for issue in result.issues)
