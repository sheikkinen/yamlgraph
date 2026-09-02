"""graph export CLI — authored Mermaid map, route overlay, route diff (FR-723).

Implements:
- graph export <graph.yaml> --mermaid [-o FILE]
- graph export <graph.yaml> --mermaid --overlay route.jsonl [-o FILE]
- graph export --diff a.jsonl b.jsonl   (exit 1 on divergence)
"""

import json
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
from yamlgraph.utils.artifact_hash import compute_artifact_hash


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

    config = yaml.safe_load(Path(args.graph_path).read_text(encoding="utf-8"))
    overlay = getattr(args, "overlay", None)
    if overlay:
        lines = Path(overlay).read_text(encoding="utf-8").splitlines()
        _validate_overlay_header(Path(args.graph_path), lines)
        route = parse_route_lines(lines)
        text = render_overlay(config, route)
    else:
        text = render_mermaid(config)

    output = getattr(args, "output", None)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(f"📁 {output}")
    else:
        print(text, end="")


def _validate_overlay_header(graph_path: Path, lines: list[str]) -> None:
    try:
        records = [json.loads(line) for line in lines if line.strip()]
    except json.JSONDecodeError as exc:
        _overlay_error(f"malformed JSON: {exc}")
    headers = [record for record in records if record.get("event") == "run"]
    if len(headers) != 1 or not records or records[0].get("event") != "run":
        _overlay_error("route overlay requires exactly one leading run header")
    actual = headers[0].get("artifact_hash")
    if not isinstance(actual, str) or not actual.startswith("sha256:"):
        _overlay_error("run header has missing or malformed artifact_hash")
    expected = compute_artifact_hash(graph_path)
    if actual != expected:
        _overlay_error(
            f"artifact hash mismatch: route log has {actual}, graph has {expected}"
        )


def _overlay_error(message: str) -> None:
    print(f"❌ invalid route overlay: {message}", file=sys.stderr)
    raise SystemExit(1)


def _run_diff(a_path: Path, b_path: Path) -> None:
    """Occurrence-aligned route diff; empty diff is the determinism witness."""
    route_a = parse_route_lines(a_path.read_text(encoding="utf-8").splitlines())
    route_b = parse_route_lines(b_path.read_text(encoding="utf-8").splitlines())
    diffs = diff_routes(route_a, route_b)
    if not diffs:
        print("✓ routes identical")
        return
    for line in diffs:
        print(line)
    sys.exit(1)
