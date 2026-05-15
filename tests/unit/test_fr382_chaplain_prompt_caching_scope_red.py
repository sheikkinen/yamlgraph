"""Acceptance tests for FR-382 prompt caching scope in Chaplain graphs."""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPLAIN_GRAPHS_DIR = REPO_ROOT / ".chaplain" / "graphs"
CONTEXT_PLANNER_PATH = (
    CHAPLAIN_GRAPHS_DIR / "watcher-enforce" / "prompts" / "context-planner.yaml"
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _resolve_prompt_path(graph_path: Path, graph: dict, prompt_name: str) -> Path:
    prompts_dir = str(graph.get("prompts_dir", "prompts"))
    if graph.get("prompts_relative", False):
        base = graph_path.parent / prompts_dir
    else:
        base = REPO_ROOT / prompts_dir
    return (base / f"{prompt_name}.yaml").resolve()


def _collect_prompt_inventory() -> dict[str, set[Path]]:
    inventory: dict[str, set[Path]] = {"llm": set(), "copilot": set()}
    for graph_path in CHAPLAIN_GRAPHS_DIR.rglob("*.yaml"):
        if "prompts" in graph_path.parts:
            continue
        graph = _load_yaml(graph_path)
        if not isinstance(graph, dict):
            continue
        nodes = graph.get("nodes")
        if not isinstance(nodes, dict):
            continue
        for node in nodes.values():
            if not isinstance(node, dict):
                continue
            node_type = node.get("type")
            prompt_name = node.get("prompt")
            if node_type in inventory and isinstance(prompt_name, str):
                inventory[node_type].add(
                    _resolve_prompt_path(graph_path, graph, prompt_name)
                )
    return inventory


@pytest.mark.req("REQ-YG-287")
def test_ac01_context_planner_uses_system_segments_with_cached_block() -> None:
    """AC-01: context-planner uses system_segments and includes cache: true."""
    prompt = _load_yaml(CONTEXT_PLANNER_PATH)
    assert "system_segments" in prompt, "context-planner must use system_segments"

    system_segments = prompt["system_segments"]
    assert isinstance(system_segments, list), "system_segments must be a list"
    assert system_segments, "system_segments must not be empty"

    cached_segments = [seg for seg in system_segments if seg.get("cache") is True]
    assert cached_segments, "context-planner must include at least one cached segment"


@pytest.mark.req("REQ-YG-289")
def test_ac02_context_planner_cached_segments_have_no_runtime_placeholders() -> None:
    """AC-02: cached system segments cannot contain runtime placeholders."""
    prompt = _load_yaml(CONTEXT_PLANNER_PATH)
    placeholder_re = re.compile(r"\{\{.*?\}\}|\{[^{}\n]+\}")

    for segment in prompt.get("system_segments", []):
        if segment.get("cache") is not True:
            continue
        content = segment.get("content", "")
        assert not placeholder_re.search(
            content
        ), "Cached system segment must not include runtime placeholders"


@pytest.mark.req("REQ-YG-287")
def test_ac03_copilot_chaplain_prompts_remain_system_field_only() -> None:
    """AC-03: Copilot-consumed prompt files remain on scalar system field."""
    inventory = _collect_prompt_inventory()

    for prompt_path in sorted(inventory["copilot"]):
        prompt = _load_yaml(prompt_path)
        assert "system" in prompt, f"{prompt_path} must retain system field"
        assert (
            "system_segments" not in prompt
        ), f"{prompt_path} must not migrate to system_segments in FR-382"


@pytest.mark.req("REQ-YG-287")
def test_ac03_prompt_inventory_scope_matches_graph_node_types() -> None:
    """Only the LLM-consumed context-planner prompt is in FR-382 scope."""
    inventory = _collect_prompt_inventory()
    expected_llm_prompt = {CONTEXT_PLANNER_PATH.resolve()}

    assert (
        inventory["llm"] == expected_llm_prompt
    ), "Only context-planner should be llm-consumed in Chaplain graphs"
    assert (
        CONTEXT_PLANNER_PATH.resolve() not in inventory["copilot"]
    ), "context-planner must not be consumed by copilot nodes"
