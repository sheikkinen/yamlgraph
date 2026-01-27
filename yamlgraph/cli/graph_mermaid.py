"""Mermaid diagram generation for graphs.

Generates Mermaid flowchart diagrams from graph configurations.
"""

import sys
from argparse import Namespace
from pathlib import Path

from yamlgraph.cli.helpers import GraphLoadError, load_graph_config


def generate_mermaid(config: dict) -> str:
    """Generate Mermaid flowchart from graph config.

    Args:
        config: Parsed YAML graph configuration

    Returns:
        Mermaid flowchart diagram as string
    """
    lines = ["```mermaid", "flowchart TD"]

    nodes = config.get("nodes", {})
    edges = config.get("edges", [])

    # Node shapes by type
    node_shapes = {
        "llm": ("[", "]"),  # Rectangle
        "prompt": ("[", "]"),
        "tool": ("[[", "]]"),  # Subroutine
        "agent": ("{{", "}}"),  # Hexagon
        "map": ("[/", "/]"),  # Parallelogram
        "subgraph": ("[[", "]]"),  # Subroutine (composition)
        "router": ("{", "}"),  # Diamond-ish
        "interrupt": ("(", ")"),  # Stadium
        "passthrough": ("([", "])"),  # Stadium
    }

    # Define nodes with shapes
    for node_name, node_config in nodes.items():
        node_type = node_config.get("type", "llm")
        left, right = node_shapes.get(node_type, ("[", "]"))
        # Escape quotes in node name for display
        display_name = node_name.replace('"', "'")
        lines.append(f'    {node_name}{left}"{display_name}"{right}')

    lines.append("")

    # Define edges
    for edge in edges:
        from_node = edge.get("from", "START")
        to_node = edge.get("to", "END")
        condition = edge.get("condition")
        edge_type = edge.get("type")

        # Map START/END to special nodes
        from_id = "__start__" if from_node == "START" else from_node

        # Handle list of targets (conditional routing)
        if isinstance(to_node, list):
            for target in to_node:
                to_id = "__end__" if target == "END" else target
                lines.append(f"    {from_id} -.-> {to_id}")
        else:
            to_id = "__end__" if to_node == "END" else to_node

            if condition:
                # Conditional edge with label
                cond_label = condition if isinstance(condition, str) else "?"
                lines.append(f"    {from_id} -->|{cond_label}| {to_id}")
            elif edge_type == "conditional":
                lines.append(f"    {from_id} -.-> {to_id}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

    lines.append("```")
    return "\n".join(lines)


def cmd_graph_mermaid(args: Namespace) -> None:
    """Generate Mermaid diagram from a graph."""
    graph_path = Path(args.graph_path)

    try:
        config = load_graph_config(graph_path)
        if config is None:
            print(f"❌ Empty YAML file: {graph_path}")
            sys.exit(1)

        mermaid = generate_mermaid(config)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(mermaid)
            print(f"✅ Mermaid diagram written to {output_path}")
        else:
            print(mermaid)

    except GraphLoadError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating mermaid: {e}")
        sys.exit(1)


__all__ = ["generate_mermaid", "cmd_graph_mermaid"]
