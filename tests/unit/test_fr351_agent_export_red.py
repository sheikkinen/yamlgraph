"""Acceptance tests for FR-351: agent-md export from skill export command."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_demo_agent_graph(tmp_path: Path) -> Path:
    graph_dir = tmp_path / "demo-agent"
    graph_dir.mkdir()

    prompts_dir = graph_dir / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "greet.yaml").write_text(
        "description: Demo greeting prompt\ntemplate: |\n  Say hello to {name}\n"
    )

    graph_path = graph_dir / "graph.yaml"
    graph_path.write_text(
        'version: "1.0"\n'
        "name: demo-agent\n"
        "description: Demo agent export graph\n"
        "prompts_relative: true\n"
        "prompts_dir: prompts\n"
        "state:\n"
        "  name:\n"
        "    type: str\n"
        "    description: Recipient name\n"
        "  result:\n"
        "    type: str\n"
        "    description: Generated greeting\n"
        "nodes:\n"
        "  generate:\n"
        "    type: llm\n"
        "    prompt: greet\n"
        "    state_key: result\n"
        "edges:\n"
        "  - from: START\n"
        "    to: generate\n"
        "  - from: generate\n"
        "    to: END\n"
    )
    return graph_path


@pytest.mark.req("REQ-YG-327")
def test_ac01_cli_registers_agent_md_format() -> None:
    from yamlgraph.cli import create_parser

    parser = create_parser()
    args = parser.parse_args(
        [
            "skill",
            "export",
            "graph.yaml",
            "--format",
            "agent-md",
            "--output-dir",
            "dist",
        ]
    )
    assert args.command == "skill"
    assert args.skill_command == "export"
    assert args.graph_path_or_dir == "graph.yaml"
    assert args.format == "agent-md"
    assert args.output_dir == "dist"


@pytest.mark.req("REQ-YG-328")
def test_ac02_export_agent_md_writes_file_in_github_agents(tmp_path: Path) -> None:
    from yamlgraph.skill_export import export_skill

    graph_path = _write_demo_agent_graph(tmp_path)
    export_skill(graph_path, format="agent-md", output_dir=tmp_path / "out")

    expected = tmp_path / "out" / ".github" / "agents" / "demo-agent.agent.md"
    assert expected.exists()
    assert expected.is_file()


@pytest.mark.req("REQ-YG-329")
@pytest.mark.req("REQ-YG-330")
def test_ac03_agent_md_contains_required_frontmatter_and_tool_scope(
    tmp_path: Path,
) -> None:
    from yamlgraph.skill_export import export_skill

    graph_path = _write_demo_agent_graph(tmp_path)
    export_skill(graph_path, format="agent-md", output_dir=tmp_path / "out")

    content = (
        tmp_path / "out" / ".github" / "agents" / "demo-agent.agent.md"
    ).read_text()
    assert content.startswith("---\n")
    assert "description: Demo agent export graph" in content
    assert "tools: [yamlgraph/*]" in content
    assert "You are demo-agent" in content
    assert "YAMLGraph MCP" in content or "yamlgraph" in content


@pytest.mark.req("REQ-YG-331")
def test_ac04_export_agent_md_errors_on_target_collision(tmp_path: Path) -> None:
    from yamlgraph.skill_export import export_skill

    graph_path = _write_demo_agent_graph(tmp_path)
    target_file = tmp_path / "out" / ".github" / "agents" / "demo-agent.agent.md"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("existing")

    with pytest.raises((FileExistsError, ValueError), match="exists|collision|target"):
        export_skill(graph_path, format="agent-md", output_dir=tmp_path / "out")


@pytest.mark.req("REQ-YG-332")
def test_ac05_docs_include_agent_md_format_and_layout() -> None:
    cli_ref = (REPO_ROOT / "reference" / "cli.md").read_text()
    skills_ref = (REPO_ROOT / "reference" / "skills-export.md").read_text()

    assert "agent-md" in cli_ref
    assert "agent-md" in skills_ref
    assert ".github/agents/" in skills_ref
    assert ".agent.md" in skills_ref
