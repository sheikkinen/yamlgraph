"""Acceptance tests for FR-382 prompt caching scope in the process graphs.

FR-1012 removed the Chaplain runtime and its context-planner prompt; the
cached-segment assertions on that prompt went with it. What remains is the
inventory contract over graphs/ (REQ-YG-287).
"""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESS_GRAPHS_DIR = REPO_ROOT / "graphs"


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
    for graph_path in PROCESS_GRAPHS_DIR.rglob("*.yaml"):
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
    """LLM-consumed process-graph prompts: world_distill's distill prompt
    (FR-744, single uncached call by design), fr_triage (FR-745) and the
    enforcement cross-check (graphs/enforcement). The context-planner prompt
    left with the runtime (FR-1012)."""
    inventory = _collect_prompt_inventory()
    world_distill_prompt = (
        PROCESS_GRAPHS_DIR / "world_distill" / "prompts" / "distill_world.yaml"
    )
    fr_triage_prompt = PROCESS_GRAPHS_DIR / "fr_triage" / "prompts" / "triage_fr.yaml"
    enforcement_prompt = PROCESS_GRAPHS_DIR / "enforcement" / "prompts" / "cross_check.yaml"
    expected_llm_prompts = {
        world_distill_prompt.resolve(),
        fr_triage_prompt.resolve(),
        enforcement_prompt.resolve(),
    }

    assert (
        inventory["llm"] == expected_llm_prompts
    ), "LLM-consumed process-graph prompts must be exactly distill_world + triage_fr + cross_check"
