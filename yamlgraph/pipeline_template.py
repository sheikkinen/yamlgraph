"""Compile-time pipeline template expansion (FR-235).

Expands `type: pipeline` meta-nodes into concrete nodes + edges
BEFORE compile_nodes() runs. The expanded nodes use existing node
factories — no new factory needed.

Follows the expand_interactive_tools() pattern from FR-049.
"""

from __future__ import annotations

import copy
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Matches {item.field_name} references in strings
_ITEM_REF_PATTERN = re.compile(r"\{item\.(\w+)\}")


def _interpolate_item_fields(value: str, item: dict[str, Any]) -> str:
    """Replace {item.field} references in a string with item values.

    Args:
        value: String potentially containing {item.field} references
        item: Item dict with field values

    Returns:
        String with all {item.field} references resolved
    """

    def replacer(match: re.Match) -> str:
        field = match.group(1)
        return str(item[field])

    return _ITEM_REF_PATTERN.sub(replacer, value)


def _interpolate_stage_config(
    stage: dict[str, Any], item: dict[str, Any]
) -> dict[str, Any]:
    """Create a concrete node config from a stage template and item.

    Interpolates {item.field} in string values of prompt, variables,
    and state_key. Non-string fields are copied verbatim.

    Args:
        stage: Stage template dict
        item: Item dict with field values

    Returns:
        Concrete node config dict (without 'name' key)
    """
    result: dict[str, Any] = {}

    for key, value in stage.items():
        if key == "name":
            continue  # 'name' is used for naming, not in node config

        if key in ("prompt", "state_key") and isinstance(value, str):
            result[key] = _interpolate_item_fields(value, item)
        elif key == "variables" and isinstance(value, dict):
            result[key] = {
                k: _interpolate_item_fields(v, item) if isinstance(v, str) else v
                for k, v in value.items()
            }
        else:
            result[key] = value

    return result


def expand_pipeline_templates(config: dict[str, Any]) -> dict[str, Any]:
    """Expand all pipeline template nodes into concrete nodes + edges.

    Transforms the config dict (on a deep copy):
    - Replaces each pipeline node with N×M concrete nodes
    - Chains stages within each item (intra-item)
    - Chains items sequentially (inter-item)
    - Rewrites external edges referencing the pipeline node

    Args:
        config: Raw graph configuration dict

    Returns:
        Modified copy of config with pipeline nodes expanded
    """
    nodes = config.get("nodes", {})

    # Find pipeline nodes
    pipeline_nodes = {
        name: cfg for name, cfg in nodes.items() if cfg.get("type") == "pipeline"
    }

    if not pipeline_nodes:
        return config

    result = copy.deepcopy(config)
    result_nodes = result["nodes"]
    result_edges = result["edges"]

    for node_name, node_config in pipeline_nodes.items():
        _expand_single(node_name, node_config, result_nodes, result_edges)

    return result


def _expand_single(
    name: str,
    config: dict[str, Any],
    nodes: dict[str, Any],
    edges: list[dict[str, Any]],
) -> None:
    """Expand a single pipeline node into concrete nodes + edges.

    Modifies nodes dict and edges list in place.

    Args:
        name: Original pipeline node name (becomes prefix)
        config: Pipeline node configuration with items and stages
        nodes: Mutable nodes dict
        edges: Mutable edges list
    """
    items = config["items"]
    stages = config["stages"]

    # Remove original pipeline node
    del nodes[name]

    # Track first and last expanded node names for edge rewriting
    first_node_name: str | None = None
    last_node_name: str | None = None

    # Previous item's last node (for inter-item chaining)
    prev_item_last: str | None = None

    internal_edges: list[dict[str, Any]] = []

    for item in items:
        item_name = item["name"]
        prev_stage_name: str | None = None

        for stage in stages:
            stage_name = stage["name"]
            expanded_name = f"{name}__{item_name}__{stage_name}"

            # Create concrete node config
            node_config = _interpolate_stage_config(stage, item)
            nodes[expanded_name] = node_config

            # Track first/last
            if first_node_name is None:
                first_node_name = expanded_name
            last_node_name = expanded_name

            # Intra-item chaining: previous stage → current stage
            if prev_stage_name is not None:
                internal_edges.append({"from": prev_stage_name, "to": expanded_name})

            prev_stage_name = expanded_name

        # Inter-item chaining: last stage of prev item → first stage of this item
        first_stage_of_item = f"{name}__{item_name}__{stages[0]['name']}"
        if prev_item_last is not None:
            internal_edges.append({"from": prev_item_last, "to": first_stage_of_item})

        prev_item_last = prev_stage_name  # last stage of current item

    # Rewrite external edges
    new_edges: list[dict[str, Any]] = []
    for edge in edges:
        new_edge = dict(edge)
        if edge.get("to") == name:
            new_edge["to"] = first_node_name
        if edge.get("from") == name:
            new_edge["from"] = last_node_name
        new_edges.append(new_edge)

    # Add internal edges
    new_edges.extend(internal_edges)

    # Replace edges in place
    edges.clear()
    edges.extend(new_edges)

    logger.info(
        f"Expanded pipeline '{name}': "
        f"{len(items)} items × {len(stages)} stages = "
        f"{len(items) * len(stages)} nodes"
    )
