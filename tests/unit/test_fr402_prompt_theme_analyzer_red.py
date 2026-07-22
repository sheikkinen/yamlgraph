"""Acceptance tests for FR-402 Prompt Theme Analyzer demo implementation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "examples" / "demos" / "prompt_theme_analyzer"
GRAPH_PATH = DEMO_DIR / "graph.yaml"
CAP_PATH = ROOT / "capabilities" / "CAP-149-prompt-theme-analyzer-demo.yaml"
DIARY_PATH = (
    ROOT
    / "docs"
    / "diary"
    / "2026-05-16-reflection-fr-402-prompt-theme-analyzer-demo.md"
)


@pytest.mark.req("REQ-YG-359")
def test_ac01_demo_scaffold_files_exist() -> None:
    required_files = [
        DEMO_DIR / "graph.yaml",
        DEMO_DIR / "tools.py",
        DEMO_DIR / "README.md",
        DEMO_DIR / "analyze.sh",
        DEMO_DIR / "demo-output.log",
        DEMO_DIR / "prompts" / "classify_theme.yaml",
        DEMO_DIR / "prompts" / "group_themes.yaml",
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Missing required file: {file_path}"


@pytest.mark.req("REQ-YG-359")
def test_ac02_list_prompts_requires_source_dir() -> None:
    from examples.demos.prompt_theme_analyzer.tools import list_prompts

    with pytest.raises(ValueError, match="source_dir is required"):
        list_prompts({})

    with pytest.raises(ValueError, match="source_dir is required"):
        list_prompts({"source_dir": ""})


@pytest.mark.req("REQ-YG-359")
def test_ac03_list_prompts_truncates_prompt_text_at_boundary(tmp_path: Path) -> None:
    from examples.demos.prompt_theme_analyzer.tools import list_prompts

    run_dir = tmp_path / "20260516-120000"
    run_dir.mkdir()
    long_text = "A" * 2500
    (run_dir / "prompts.txt").write_text(long_text, encoding="utf-8")

    result = list_prompts({"source_dir": str(tmp_path)})
    assert len(result["prompt_entries"]) == 1
    entry = result["prompt_entries"][0]
    assert entry["timestamp"] == "20260516-120000"
    assert len(entry["text"]) == 2000
    assert entry["text"] == "A" * 2000


@pytest.mark.req("REQ-YG-359")
def test_ac04_graph_has_python_aggregate_between_map_and_group() -> None:
    from yamlgraph.compile.graph_loader import load_graph_config

    config = load_graph_config(str(GRAPH_PATH))
    assert config.nodes["classify_themes"]["type"] == "map"
    assert config.nodes["aggregate_themes"]["type"] == "python"
    assert config.nodes["group_themes"]["type"] == "llm"

    edge_pairs = {(edge["from"], edge["to"]) for edge in config.edges}
    assert ("classify_themes", "aggregate_themes") in edge_pairs
    assert ("aggregate_themes", "group_themes") in edge_pairs
    assert ("classify_themes", "group_themes") not in edge_pairs


@pytest.mark.req("REQ-YG-359")
def test_ac05_group_prompt_uses_aggregated_counts() -> None:
    from yamlgraph.compile.graph_loader import load_graph_config

    config = load_graph_config(str(GRAPH_PATH))
    group_node = config.nodes["group_themes"]
    assert group_node["variables"]["theme_counts"] == "{state.theme_counts}"

    prompt = yaml.safe_load((DEMO_DIR / "prompts" / "group_themes.yaml").read_text())
    rendered_body = (prompt.get("user") or "") + (prompt.get("template") or "")
    assert "theme_counts" in rendered_body
    assert "classifications_json" not in rendered_body


@pytest.mark.req("REQ-YG-359")
def test_ac06_graph_lints_clean() -> None:
    from yamlgraph.linter.graph_linter import lint_graph

    result = lint_graph(GRAPH_PATH)
    errors = [issue for issue in result.issues if issue.severity == "error"]
    assert errors == [], f"Lint errors: {errors}"


@pytest.mark.req("REQ-YG-359")
def test_ac07_demo_output_log_proves_integration_run() -> None:
    log_path = DEMO_DIR / "demo-output.log"
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert (
        "yamlgraph graph run examples/demos/prompt_theme_analyzer/graph.yaml" in content
    )
    assert "Graph execution completed successfully" in content


@pytest.mark.req("REQ-YG-359")
def test_ac08_list_prompts_filters_empty_or_invalid_inputs(tmp_path: Path) -> None:
    from examples.demos.prompt_theme_analyzer.tools import list_prompts

    valid_dir = tmp_path / "20260516-valid"
    valid_dir.mkdir()
    (valid_dir / "prompts.txt").write_text(
        "Highly detailed fantasy portrait with ornate armor and dramatic lighting."
    )

    short_dir = tmp_path / "20260516-short"
    short_dir.mkdir()
    (short_dir / "prompts.txt").write_text("short")

    dump_dir = tmp_path / "20260516-dump"
    dump_dir.mkdir()
    (dump_dir / "prompts.txt").write_text("{_map_index: 1, error: true}")

    refusal_dir = tmp_path / "20260516-refusal"
    refusal_dir.mkdir()
    (refusal_dir / "prompts.txt").write_text(
        "I'm sorry, but I can't help with that request."
    )

    result = list_prompts({"source_dir": str(tmp_path)})
    assert len(result["prompt_entries"]) == 1
    assert result["prompt_entries"][0]["timestamp"] == "20260516-valid"


@pytest.mark.req("REQ-YG-359")
def test_ac08_aggregate_themes_is_deterministic_and_counts_correctly() -> None:
    from examples.demos.prompt_theme_analyzer.tools import aggregate_themes

    classifications = [
        {"timestamp": "t1", "theme": " Dark   Gothic Romance "},
        {"timestamp": "t2", "theme": "Cyberpunk Warrior Portrait"},
        {"timestamp": "t3", "theme": "Dark Gothic Romance"},
        {"timestamp": "t4", "theme": "Cyberpunk Warrior Portrait"},
        {"timestamp": "t5", "theme": ""},
        {"timestamp": "t6", "theme": None},
        "invalid",
    ]

    expected = [
        {"theme": "Cyberpunk Warrior Portrait", "count": 2},
        {"theme": "Dark Gothic Romance", "count": 2},
    ]
    assert (
        aggregate_themes({"classifications": classifications})["theme_counts"]
        == expected
    )
    assert (
        aggregate_themes({"classifications": list(reversed(classifications))})[
            "theme_counts"
        ]
        == expected
    )


@pytest.mark.req("REQ-YG-359")
def test_ac08_write_report_produces_required_markdown_sections(tmp_path: Path) -> None:
    from examples.demos.prompt_theme_analyzer.tools import write_report

    output_path = tmp_path / "prompt-theme-report.md"
    result = write_report(
        {
            "theme_counts": [
                {"theme": "Cyberpunk Warrior Portrait", "count": 4},
                {"theme": "Dark Gothic Romance", "count": 3},
            ],
            "theme_groups": {
                "grouped_themes_markdown": (
                    "- **Noir & Gothic**: Dark Gothic Romance\n"
                    "- **Futurist Portraits**: Cyberpunk Warrior Portrait"
                ),
                "total_classified": 7,
            },
            "output_path": str(output_path),
        }
    )

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "## Deterministic Theme Counts" in content
    assert "| Theme | Count |" in content
    assert "## LLM Grouped Theme Clusters" in content
    assert "Noir & Gothic" in content
    assert "Total classified prompts: **7**" in content
    assert result["output_path"] == str(output_path)


@pytest.mark.req("REQ-YG-359")
def test_ac09_capability_registry_contains_cap149_req359() -> None:
    assert CAP_PATH.exists()
    cap = CAP_PATH.read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "id: CAP-149" in cap
    assert "REQ-YG-359" in cap
    assert "REQ-YG-359" in architecture
    assert "CAP-149" in architecture


@pytest.mark.req("REQ-YG-359")
def test_ac10_diary_entry_exists() -> None:
    assert DIARY_PATH.exists()
    content = DIARY_PATH.read_text(encoding="utf-8")
    assert "Seed:" in content
