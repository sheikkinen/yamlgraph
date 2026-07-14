"""graph export CLI — authored Mermaid map, route overlay, route diff (FR-723).

Implements:
- graph export <graph.yaml> --mermaid [-o FILE]
- graph export <graph.yaml> --mermaid --overlay route.jsonl [-o FILE]
- graph export --diff a.jsonl b.jsonl   (exit 1 on divergence)
"""

import sys
from argparse import Namespace
from pathlib import Path

import yaml

from yamlgraph.mermaid_export import (
    diff_routes,
    parse_route_lines,
    render_mermaid,
    render_overlay,
)


def cmd_graph_export(args: Namespace) -> None:
    """Export the authored graph as Mermaid, overlay a route, or diff routes."""
    diff = getattr(args, "diff", None)
    if diff:
        _run_diff(Path(diff[0]), Path(diff[1]))
        return

    if not getattr(args, "graph_path", None):
        print(
            "❌ graph export requires a graph path (or --diff A B)",
            file=sys.stderr,
        )
        sys.exit(2)
    if not getattr(args, "mermaid", False):
        print(
            "❌ graph export supports --mermaid (optionally with --overlay) "
            "or --diff A B",
            file=sys.stderr,
        )
        sys.exit(2)

    config = yaml.safe_load(Path(args.graph_path).read_text())
    overlay = getattr(args, "overlay", None)
    if overlay:
        route = parse_route_lines(Path(overlay).read_text().splitlines())
        text = render_overlay(config, route)
    else:
        text = render_mermaid(config)

    output = getattr(args, "output", None)
    if output:
        Path(output).write_text(text)
        print(f"📁 {output}")
    else:
        print(text, end="")


def _run_diff(a_path: Path, b_path: Path) -> None:
    """Occurrence-aligned route diff; empty diff is the determinism witness."""
    route_a = parse_route_lines(a_path.read_text().splitlines())
    route_b = parse_route_lines(b_path.read_text().splitlines())
    diffs = diff_routes(route_a, route_b)
    if not diffs:
        print("✓ routes identical")
        return
    for line in diffs:
        print(line)
    sys.exit(1)
