"""Acceptance tests for FR-382 prompt caching scope in Chaplain graphs."""

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPLAIN_GRAPHS_DIR = REPO_ROOT / ".chaplain" / "graphs"
# FR-1011: fr_triage and world_distill were relocated to graphs/; the process-graph
# inventory spans both roots until Phase 2 removes .chaplain/.
PROCESS_GRAPHS_DIR = REPO_ROOT / "graphs"
CONTEXT_PLANNER_PATH = (
    CHAPLAIN_GRAPHS_DIR / "watcher-enforce" / "prompts" / "context-planner.yaml"
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _resolve_prompt_path(graph_path: Path, graph: dict, prompt_name: str) -> Path:
    prompts_dir = str(graph.get("prompts_dir", "prompts"))
    if graph.get("prompts_relative", False):
        base = graph_path.parent / prompts_dir
    else:
        base = REPO_ROOT / prompts_dir
    return (base / f"{prompt_name}.yaml").resolve()


def _collect_prompt_inventory() -> dict[str, set[Path]]:
    inventory: dict[str, set[Path]] = {"llm": set(), "copilot": set()}
    graph_paths = [*CHAPLAIN_GRAPHS_DIR.rglob("*.yaml"), *PROCESS_GRAPHS_DIR.rglob("*.yaml")]
    for graph_path in graph_paths:
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
    """LLM-consumed process-graph prompts: context-planner (FR-382 caching
    scope) + world_distill's distill prompt (FR-744, out of FR-382
    caching scope — single uncached call by design) + fr_triage (FR-745)
    + the enforcement cross-check (graphs/enforcement). FR-1011 moved the
    first two live graphs to graphs/."""
    inventory = _collect_prompt_inventory()
    world_distill_prompt = (
        PROCESS_GRAPHS_DIR / "world_distill" / "prompts" / "distill_world.yaml"
    )
    fr_triage_prompt = PROCESS_GRAPHS_DIR / "fr_triage" / "prompts" / "triage_fr.yaml"
    enforcement_prompt = PROCESS_GRAPHS_DIR / "enforcement" / "prompts" / "cross_check.yaml"
    expected_llm_prompts = {
        CONTEXT_PLANNER_PATH.resolve(),
        world_distill_prompt.resolve(),
        fr_triage_prompt.resolve(),
        enforcement_prompt.resolve(),
    }

    assert (
        inventory["llm"] == expected_llm_prompts
    ), "LLM-consumed process-graph prompts must be exactly context-planner + distill_world + triage_fr + cross_check"
    assert (
        CONTEXT_PLANNER_PATH.resolve() not in inventory["copilot"]
    ), "context-planner must not be consumed by copilot nodes"
