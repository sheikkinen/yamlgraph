"""Acceptance tests for FR-348: portable skill export packaging."""

from __future__ import annotations

import json
import os
from argparse import Namespace
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_demo_skill_graph(tmp_path: Path) -> Path:
    graph_dir = tmp_path / "demo-skill"
    graph_dir.mkdir()
    prompts_dir = graph_dir / "prompts"
    prompts_dir.mkdir()

    (prompts_dir / "greet.yaml").write_text(
        "description: Demo greeting prompt\n"
        "template: |\n"
        "  Write a short greeting for {topic}\n"
        "user: |\n"
        "  Write a short greeting for {topic}\n"
    )

    graph_path = graph_dir / "graph.yaml"
    graph_path.write_text(
        'version: "1.0"\n'
        "name: demo-skill\n"
        "description: Demo skill export graph\n"
        "prompts_relative: true\n"
        "prompts_dir: prompts\n"
        "state:\n"
        "  topic:\n"
        "    type: str\n"
        "    description: Topic for the skill\n"
        "  result:\n"
        "    type: str\n"
        "    description: Generated output\n"
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


@pytest.mark.req("REQ-YG-320")
def test_ac01_cli_registers_skill_export_subcommand() -> None:
    from yamlgraph.cli import create_parser

    parser = create_parser()
    args = parser.parse_args(
        [
            "skill",
            "export",
            "graph.yaml",
            "--format",
            "copilot",
            "--output-dir",
            "dist",
        ]
    )
    assert args.command == "skill"
    assert args.skill_command == "export"
    assert args.graph_path_or_dir == "graph.yaml"
    assert args.format == "copilot"
    assert args.output_dir == "dist"


@pytest.mark.req("REQ-YG-321")
def test_ac02_export_generates_required_skill_package_files(tmp_path: Path) -> None:
    from yamlgraph.export.skill import export_skill

    graph_path = _write_demo_skill_graph(tmp_path)
    package = export_skill(
        graph_path, format="skill-md", output_dir=tmp_path / "output"
    )
    target = package.target_dir

    assert (target / "SKILL.md").exists()
    run_script = target / "scripts" / "run.sh"
    assert run_script.exists()
    assert os.access(run_script, os.X_OK)
    assert (target / "assets" / "schema.json").exists()
    references_dir = target / "references"
    assert references_dir.exists() and references_dir.is_dir()
    prompt_ref = references_dir / "greet.md"
    assert prompt_ref.exists()
    prompt_ref_content = prompt_ref.read_text()
    assert "## Description" in prompt_ref_content
    assert "## Template" in prompt_ref_content

    run_script_content = run_script.read_text()
    assert "yamlgraph graph run" in run_script_content
    assert "--var topic=example" in run_script_content


@pytest.mark.req("REQ-YG-322")
def test_ac03_skill_md_contains_graph_metadata_and_run_instructions(
    tmp_path: Path,
) -> None:
    from yamlgraph.export.skill import export_skill

    graph_path = _write_demo_skill_graph(tmp_path)
    package = export_skill(graph_path, output_dir=tmp_path / "out")
    content = (package.target_dir / "SKILL.md").read_text()

    assert content.startswith("# demo-skill")
    assert "Demo skill export graph" in content
    assert "## Inputs" in content
    assert "`topic` (`string`): Topic for the skill" in content
    assert "## Outputs" in content
    assert "`result` (`string`)" in content
    assert "## Run" in content
    assert "yamlgraph graph run" in content


@pytest.mark.req("REQ-YG-323")
def test_ac04_schema_json_contains_input_and_output_sections(tmp_path: Path) -> None:
    from yamlgraph.export.skill import export_skill

    graph_path = _write_demo_skill_graph(tmp_path)
    package = export_skill(graph_path, output_dir=tmp_path / "out")
    schema = json.loads((package.target_dir / "assets" / "schema.json").read_text())

    assert "input" in schema
    assert "output" in schema
    assert schema["input"]["properties"]["topic"]["type"] == "string"
    assert "topic" in schema["input"]["required"]
    assert schema["output"]["properties"]["result"]["type"] == "string"
    assert "result" in schema["output"]["required"]


@pytest.mark.req("REQ-YG-324")
def test_ac05_format_variant_paths_skill_md_copilot_cursor(tmp_path: Path) -> None:
    from yamlgraph.export.skill import export_skill

    graph_path = _write_demo_skill_graph(tmp_path)

    pkg_skill_md = export_skill(
        graph_path,
        format="skill-md",
        output_dir=tmp_path / "skill-md-output",
    )
    assert pkg_skill_md.target_dir == tmp_path / "skill-md-output" / "demo-skill"

    pkg_copilot = export_skill(
        graph_path,
        format="copilot",
        output_dir=tmp_path / "copilot-output",
    )
    assert pkg_copilot.target_dir == (
        tmp_path / "copilot-output" / ".copilot" / "skills" / "demo-skill"
    )

    pkg_cursor = export_skill(
        graph_path,
        format="cursor",
        output_dir=tmp_path / "cursor-output",
    )
    assert pkg_cursor.target_dir == (
        tmp_path / "cursor-output" / ".cursor" / "skills" / "demo-skill"
    )


@pytest.mark.req("REQ-YG-325")
def test_ac06_export_errors_on_invalid_graph_or_target_collision(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from yamlgraph.cli.skill_commands import cmd_skill_export
    from yamlgraph.export.skill import export_skill

    with pytest.raises(ValueError, match="Graph path does not exist"):
        export_skill(tmp_path / "missing-graph.yaml", output_dir=tmp_path / "out")

    graph_path = _write_demo_skill_graph(tmp_path)
    with pytest.raises(ValueError, match="Unsupported format"):
        export_skill(
            graph_path, format="unsupported-format", output_dir=tmp_path / "out"
        )

    collision_target = tmp_path / "collision-output" / "demo-skill"
    collision_target.mkdir(parents=True)
    (collision_target / "existing.txt").write_text("collision")
    with pytest.raises(FileExistsError, match="already exists and is not empty"):
        export_skill(
            graph_path, format="skill-md", output_dir=tmp_path / "collision-output"
        )

    args = Namespace(
        graph_path_or_dir=str(tmp_path / "missing-graph.yaml"),
        format="skill-md",
        output_dir=str(tmp_path / "cli-out"),
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_skill_export(args)
    assert exc_info.value.code == 1
    assert "Error exporting skill" in capsys.readouterr().out


@pytest.mark.req("REQ-YG-326")
def test_ac07_cli_reference_docs_include_skill_export_usage() -> None:
    cli_ref = (REPO_ROOT / "reference" / "cli.md").read_text()
    skill_ref = (REPO_ROOT / "reference" / "skills-export.md").read_text()
    readme_ref = (REPO_ROOT / "reference" / "README.md").read_text()

    assert "yamlgraph skill export" in cli_ref
    assert "--format" in cli_ref
    assert "skill-md" in cli_ref and "copilot" in cli_ref and "cursor" in cli_ref

    assert "yamlgraph skill export" in skill_ref
    assert "SKILL.md" in skill_ref
    assert "scripts/run.sh" in skill_ref
    assert "assets/schema.json" in skill_ref
    assert "references/" in skill_ref
    assert ".copilot/skills/" in skill_ref
    assert ".cursor/skills/" in skill_ref

    assert "skills-export.md" in readme_ref
