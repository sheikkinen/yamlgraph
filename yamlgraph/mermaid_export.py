"""Authored-graph Mermaid export, route overlay, occurrence-aligned diff (FR-723).

Pure functions of the graph YAML dict and route.jsonl lines: stdlib only —
no LLM, no API keys, no network — safe for pre-commit use by downstream
projects.

Renders the AUTHORED view (typed nodes, condition labels by reference,
router routes, loop limits, explicit loop-exit edges, interrupt marks),
not the compiled LangGraph view (``draw_mermaid()`` renders Send fan-outs
and internal names — the documented, rejected alternative).
"""

from __future__ import annotations

import json
from collections import Counter
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

__all__ = [
    "render_mermaid",
    "render_overlay",
    "parse_route_lines",
    "diff_routes",
]

_TAKEN_STYLE = "stroke:#e11,stroke-width:3px"


@dataclass
class _Edge:
    source: str
    target: str
    label: str | None = None
    dashed: bool = False


def _esc(label: str) -> str:
    """Mermaid label escape: quotes delimit, pipes split — replace both."""
    return label.replace('"', "'").replace("|", "/")


def _node_line(name: str, node: dict, loop_limits: dict[str, int]) -> str:
    node_type = (node or {}).get("type") or "llm"
    parts = [node_type]
    if name in loop_limits:
        parts.append(f"loop≤{loop_limits[name]}")
    suffix = ":::interrupt" if node_type == "interrupt" else ""
    return f'    {name}["{name} ({", ".join(parts)})"]{suffix}'


def _authored_edges(config: dict) -> list[_Edge]:
    """Flatten the authored YAML into renderable edges.

    Covers: plain edges, condition-labelled edges, router fan-outs
    (labelled by route key), and explicit loop-exit edges — the seam this
    FR closes deserves visibility on the authored map.
    """
    nodes: dict[str, Any] = config.get("nodes") or {}
    loop_limits: dict[str, int] = config.get("loop_limits") or {}
    loop_exits: dict[str, str] = config.get("loop_exits") or {}
    edges: list[_Edge] = []

    for edge in config.get("edges") or []:
        source = edge.get("from")
        targets = edge.get("to")
        condition = edge.get("condition")
        targets = targets if isinstance(targets, list) else [targets]
        routes = (nodes.get(source) or {}).get("routes") or {}
        route_labels = {target: key for key, target in routes.items()}
        for target in targets:
            label = condition or route_labels.get(target)
            edges.append(_Edge(source, target, label))

    for source in loop_limits:
        edges.append(
            _Edge(source, loop_exits.get(source, "END"), "loop_exit", dashed=True)
        )
    return edges


def _edge_line(edge: _Edge) -> str:
    arrow = "-.->" if edge.dashed else "-->"
    label = f'|"{_esc(edge.label)}"|' if edge.label else ""
    return f"    {edge.source} {arrow}{label} {edge.target}"


def render_mermaid(config: dict) -> str:
    """Render the authored graph YAML as a Mermaid flowchart."""
    nodes: dict[str, Any] = config.get("nodes") or {}
    loop_limits: dict[str, int] = config.get("loop_limits") or {}

    lines = ["flowchart TD", "    START((START))"]
    lines += [_node_line(name, node, loop_limits) for name, node in nodes.items()]
    lines.append("    END((END))")
    lines += [_edge_line(edge) for edge in _authored_edges(config)]

    if any((node or {}).get("type") == "interrupt" for node in nodes.values()):
        lines.append("    classDef interrupt stroke-dasharray: 5 5")
    return "\n".join(lines) + "\n"


def render_overlay(config: dict, route: list[dict]) -> str:
    """Render an executed route on the authored map.

    Taken edges are highlighted and carry decision ordinals (``#N``) so the
    ordered route is reconstructible from the render alone — counts alone
    violate ``assert_path_not_destination`` in the tool that exists to
    serve it (AC-03 condemning test).
    """
    nodes: dict[str, Any] = config.get("nodes") or {}
    loop_limits: dict[str, int] = config.get("loop_limits") or {}
    edges = _authored_edges(config)

    # Ordinals per (source, target); loop_exit decisions bind to the
    # dashed loop-exit edge, everything else to the authored edge.
    ordinals: dict[tuple[str, str, bool], list[int]] = {}
    for i, entry in enumerate(route, 1):
        dashed = entry.get("value") == "loop_exit"
        key = (entry["node"], entry["target"], dashed)
        ordinals.setdefault(key, []).append(i)

    keyed = {(e.source, e.target, e.dashed): e for e in edges}
    for key in ordinals:
        if key not in keyed:  # decision on an edge the YAML never authored
            source, target, dashed = key
            synthetic = _Edge(source, target, None, dashed)
            edges.append(synthetic)
            keyed[key] = synthetic

    lines = ["flowchart TD", "    START((START))"]
    lines += [_node_line(name, node, loop_limits) for name, node in nodes.items()]
    lines.append("    END((END))")

    taken_links: list[int] = []
    for index, edge in enumerate(edges):
        marks = ordinals.get((edge.source, edge.target, edge.dashed))
        if marks:
            taken_links.append(index)
            suffix = " ".join(f"#{n}" for n in marks)
            label = f"{edge.label} {suffix}" if edge.label else suffix
            edge = _Edge(edge.source, edge.target, label, edge.dashed)
        lines.append(_edge_line(edge))

    taken_nodes = sorted({e["node"] for e in route} | {e["target"] for e in route})
    lines.append("    classDef taken stroke:#e11,stroke-width:3px")
    if taken_nodes:
        lines.append(f"    class {','.join(taken_nodes)} taken")
    lines += [f"    linkStyle {i} {_TAKEN_STYLE}" for i in taken_links]
    return "\n".join(lines) + "\n"


def parse_route_lines(lines: list[str]) -> list[dict]:
    """Parse route.jsonl lines tolerantly.

    Accepts raw JSON lines and logging-prefixed lines; anything that is not
    an ``event: route`` object is skipped (forensic logs are shared files).
    """
    out: list[dict] = []
    for line in lines:
        start = line.find("{")
        if start == -1:
            continue
        with suppress(ValueError):
            obj = json.loads(line[start:])
            if isinstance(obj, dict) and obj.get("event") == "route":
                out.append(obj)
    return out


def _fmt(entry: dict) -> str:
    text = f"{entry.get('value')} -> {entry.get('target')}"
    if entry.get("fan_out") is not None:
        text += f" (fan_out={entry['fan_out']})"
    return text


def diff_routes(a: list[dict], b: list[dict]) -> list[str]:
    """Occurrence-aligned route diff (AC-04).

    Decisions are keyed per ``(node, occurrence_index)`` — naive positional
    diff misaligns after the first divergence in a loopy route (NC-373 R-3).
    Empty result = the cheap determinism witness.
    """

    def keyed(route: list[dict]) -> dict[tuple[str, int], dict]:
        counts: Counter[str] = Counter()
        out: dict[tuple[str, int], dict] = {}
        for entry in route:
            counts[entry["node"]] += 1
            out[(entry["node"], counts[entry["node"]])] = entry
        return out

    keyed_a, keyed_b = keyed(a), keyed(b)
    diffs: list[str] = []
    for node, occurrence in sorted(set(keyed_a) | set(keyed_b)):
        entry_a = keyed_a.get((node, occurrence))
        entry_b = keyed_b.get((node, occurrence))
        seam = f"{node}#{occurrence}"
        if entry_b is None:
            diffs.append(f"{seam}: only in a — {_fmt(entry_a)}")
        elif entry_a is None:
            diffs.append(f"{seam}: only in b — {_fmt(entry_b)}")
        elif (
            entry_a.get("value"),
            entry_a.get("target"),
            entry_a.get("fan_out"),
        ) != (entry_b.get("value"), entry_b.get("target"), entry_b.get("fan_out")):
            diffs.append(f"{seam}: {_fmt(entry_a)} (a) vs {_fmt(entry_b)} (b)")
    return diffs
