"""Acceptance tests for FR-350: agent-md export with YAMLGraph tool scoping."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_demo_agent_graph(tmp_path: Path) -> Path:
    graph_dir = tmp_path / "hello-agent"
    graph_dir.mkdir()
    prompts_dir = graph_dir / "prompts"
    prompts_dir.mkdir()

    (prompts_dir / "greet.yaml").write_text(
        "description: Demo greeting prompt\n"
        "template: |\n"
        "  Write a short greeting for {name} in {style} style.\n"
        "user: |\n"
        "  Write a short greeting for {name} in {style} style.\n"
    )

    graph_path = graph_dir / "graph.yaml"
    graph_path.write_text(
        'version: "1.0"\n'
        "name: hello-world\n"
        "description: Friendly greeting agent for YAMLGraph demos.\n"
        "prompts_relative: true\n"
        "prompts_dir: prompts\n"
        "state:\n"
        "  name:\n"
        "    type: str\n"
        "    description: Name to greet\n"
        "  style:\n"
        "    type: str\n"
        "    description: Writing style\n"
        "  result:\n"
        "    type: str\n"
        "    description: Final greeting output\n"
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


def _parse_frontmatter(agent_md: str) -> dict[str, object]:
    _, frontmatter_block, _ = agent_md.split("---", 2)
    payload = yaml.safe_load(frontmatter_block)
    assert isinstance(payload, dict)
    return payload


@pytest.mark.req("REQ-YG-327")
def test_ac01_cli_registers_agent_md_format_for_skill_export() -> None:
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
def test_ac02_agent_md_format_writes_expected_github_agents_path(
    tmp_path: Path,
) -> None:
    from yamlgraph.export.skill import export_skill

    graph_path = _write_demo_agent_graph(tmp_path)
    package = export_skill(
        graph_path, format="agent-md", output_dir=tmp_path / "output"
    )
    expected = tmp_path / "output" / ".github" / "agents" / "hello-world.agent.md"

    assert package.target_dir == expected.parent
    assert package.target_file == expected
    assert expected.exists()


@pytest.mark.req("REQ-YG-329")
def test_ac03_agent_md_frontmatter_contains_description_tools_and_model(
    tmp_path: Path,
) -> None:
    from yamlgraph.export.skill import export_skill

    graph_path = _write_demo_agent_graph(tmp_path)
    package = export_skill(
        graph_path, format="agent-md", output_dir=tmp_path / "output"
    )
    assert package.target_file is not None

    payload = _parse_frontmatter(package.target_file.read_text())
    assert isinstance(payload.get("description"), str)
    assert payload["description"]
    assert payload["tools"] == ["yamlgraph/*"]
    assert payload["model"] == "Claude Sonnet 4"


@pytest.mark.req("REQ-YG-330")
def test_ac04_agent_md_body_contains_inputs_and_invocation_guidance(
    tmp_path: Path,
) -> None:
    from yamlgraph.export.skill import export_skill

    graph_path = _write_demo_agent_graph(tmp_path)
    package = export_skill(
        graph_path, format="agent-md", output_dir=tmp_path / "output"
    )
    assert package.target_file is not None
    content = package.target_file.read_text()

    assert "# hello-world" in content
    assert "## Inputs" in content
    assert "`name` (`string`): Name to greet" in content
    assert "`style` (`string`): Writing style" in content
    assert "## Invocation" in content
    assert "@hello-world" in content


@pytest.mark.req("REQ-YG-331")
def test_ac05_agent_md_export_errors_on_invalid_graph_format_or_collision(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.skill_commands import cmd_skill_export
    from yamlgraph.export.skill import export_skill

    with pytest.raises(ValueError, match="Graph path does not exist"):
        export_skill(tmp_path / "missing-graph.yaml", format="agent-md")

    graph_path = _write_demo_agent_graph(tmp_path)
    with pytest.raises(ValueError, match="Unsupported format"):
        export_skill(
            graph_path, format="unsupported-format", output_dir=tmp_path / "out"
        )

    collision_file = (
        tmp_path / "collision" / ".github" / "agents" / "hello-world.agent.md"
    )
    collision_file.parent.mkdir(parents=True)
    collision_file.write_text("existing")
    with pytest.raises(FileExistsError, match="Output target file already exists"):
        export_skill(graph_path, format="agent-md", output_dir=tmp_path / "collision")

    args = Namespace(
        graph_path_or_dir=str(tmp_path / "missing-graph.yaml"),
        format="agent-md",
        output_dir=str(tmp_path / "cli-out"),
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_skill_export(args)
    assert exc_info.value.code == 1
    assert "Error exporting skill" in capsys.readouterr().out


@pytest.mark.req("REQ-YG-332")
def test_ac06_docs_include_agent_md_usage_examples() -> None:
    cli_ref = (REPO_ROOT / "reference" / "cli.md").read_text()
    skill_ref = (REPO_ROOT / "reference" / "skills-export.md").read_text()
    readme_ref = (REPO_ROOT / "reference" / "README.md").read_text()

    assert "agent-md" in cli_ref
    assert ".github/agents" in cli_ref
    assert ".agent.md" in cli_ref

    assert "agent-md" in skill_ref
    assert ".github/agents" in skill_ref
    assert ".agent.md" in skill_ref

    assert "skills-export.md" in readme_ref
    assert "agent-md" in readme_ref
