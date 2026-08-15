"""FR-797 relay-capable subgraph detection and state-field synthesis.

Shared by the runtime state builder, the codegen path, and the node
factory — the single source of truth for what makes a subgraph node
relay-capable and which internal fields the two-node split requires.
"""

from pathlib import Path
from typing import Any

import yaml


def subgraph_relay_capable(node_config: dict, source_path: Path | None = None) -> bool:
    """FR-797: can this subgraph node's child interrupt (relay-capable)?

    True for invoke-mode subgraph nodes when interrupt_output_mapping is
    configured OR the child graph declares a ``type: interrupt`` node
    (resolvable only when the parent's source_path is known).
    """
    if node_config.get("type") != "subgraph":
        return False
    if node_config.get("mode", "invoke") != "invoke":
        return False
    if node_config.get("interrupt_output_mapping"):
        return True
    graph_rel = node_config.get("graph")
    if not source_path or not graph_rel:
        return False
    child_path = (Path(source_path).parent / graph_rel).resolve()
    if not child_path.exists():
        return False
    child = yaml.safe_load(child_path.read_text()) or {}
    child_nodes = child.get("nodes") or {}
    return any(
        isinstance(n, dict) and n.get("type") == "interrupt"
        for n in child_nodes.values()
    )


def relay_field_names(node_name: str) -> tuple[str, str, str]:
    """FR-797 relay internals for one subgraph node (paused, payload, resume)."""
    return (
        f"__{node_name}_paused__",
        f"__{node_name}_payload__",
        f"__{node_name}_resume__",
    )


def relay_state_fields(node_name: str) -> dict[str, type]:
    """Runtime TypedDict fields for one relay-capable subgraph node."""
    paused, payload, resume = relay_field_names(node_name)
    return {paused: bool, payload: Any, resume: Any}


def relay_codegen_fields(node_name: str) -> dict[str, str]:
    """Codegen field annotations for one relay-capable subgraph node."""
    paused, payload, resume = relay_field_names(node_name)
    return {paused: "bool", payload: "Any", resume: "Any"}
