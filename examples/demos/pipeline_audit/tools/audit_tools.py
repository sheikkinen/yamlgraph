"""Pipeline audit tools — scan graph YAMLs and Python nodes for structural patterns."""

from __future__ import annotations

import glob
import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SCAN_DIRS = [
    "graphs/*.yaml",
    "examples/**/graph.yaml",
    "examples/**/*.yaml",
    "projects/**/graph.yaml",
    "projects/**/*.yaml",
]

QUALITY_KEYWORDS = {"evaluate", "review", "grade", "score", "validate", "judge"}


# ---------------------------------------------------------------------------
# Tool: scan_graphs
# ---------------------------------------------------------------------------


def scan_graphs_tool(scan_dir: str = "") -> str:
    """Discover and parse all graph YAML files, returning structure summary."""
    patterns = (
        [f"{scan_dir}/**/graph.yaml", f"{scan_dir}/**/*.yaml"]
        if scan_dir and scan_dir != "None"
        else DEFAULT_SCAN_DIRS
    )

    graphs: list[dict] = []
    seen: set[str] = set()

    for pattern in patterns:
        for path_str in sorted(glob.glob(pattern, recursive=True)):
            real = str(Path(path_str).resolve())
            if real in seen:
                continue
            seen.add(real)

            try:
                with open(path_str, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                if not isinstance(config, dict) or "nodes" not in config:
                    continue
                graphs.append(_parse_graph(path_str, config))
            except Exception:
                continue

    if not graphs:
        return "No graphs found."

    lines = [f"# Pipeline Inventory ({len(graphs)} graphs)\n"]
    for g in graphs:
        lines.append(f"## {g['name']} — {g['path']}")
        lines.append(f"  Description: {g['description']}")
        lines.append(f"  Nodes: {g['node_count']} ({', '.join(g['node_types'])})")
        if g["map_nodes"]:
            lines.append(f"  Map nodes: {', '.join(g['map_nodes'])}")
        if g["on_error_skip"]:
            lines.append(f"  on_error:skip: {', '.join(g['on_error_skip'])}")
        if g["quality_gates"]:
            lines.append(f"  Quality gates: {', '.join(g['quality_gates'])}")
        else:
            lines.append("  Quality gates: NONE")
        if g["loops"]:
            lines.append(f"  Loops: {', '.join(g['loops'])}")
        lines.append("")

    return "\n".join(lines)


def _parse_graph(path: str, config: dict) -> dict:
    """Extract structural info from a parsed graph config."""
    name = config.get("name", Path(path).parent.name)
    desc = config.get("description", "")
    nodes = config.get("nodes", {})

    node_types: list[str] = []
    map_nodes: list[str] = []
    on_error_skip: list[str] = []
    quality_gates: list[str] = []
    loops: list[str] = []

    for node_name, node_cfg in nodes.items():
        if not isinstance(node_cfg, dict):
            continue
        ntype = node_cfg.get("type", "llm")
        node_types.append(f"{node_name}:{ntype}")

        if ntype == "map":
            map_nodes.append(node_name)
        if node_cfg.get("on_error") == "skip":
            on_error_skip.append(node_name)

        # Detect quality gate nodes by name or prompt reference
        name_lower = node_name.lower()
        prompt_lower = str(node_cfg.get("prompt", "")).lower()
        if name_lower in QUALITY_KEYWORDS or any(
            kw in name_lower for kw in QUALITY_KEYWORDS
        ):
            quality_gates.append(node_name)
        elif any(kw in prompt_lower for kw in QUALITY_KEYWORDS):
            quality_gates.append(f"{node_name} (via prompt)")

    # Detect loops from edges
    edges = config.get("edges", [])
    edge_targets = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        src = edge.get("from", "")
        dst = edge.get("to", "")
        edge_targets.setdefault(src, []).append(dst)

    # Simple cycle detection: if a node appears as both source and target
    all_sources = set(edge_targets.keys())
    for src, dsts in edge_targets.items():
        for dst in dsts:
            if dst in all_sources and src in edge_targets.get(dst, []):
                loops.append(f"{src} ↔ {dst}")

    return {
        "name": name,
        "path": path,
        "description": desc,
        "node_count": len(nodes),
        "node_types": node_types,
        "map_nodes": map_nodes,
        "on_error_skip": on_error_skip,
        "quality_gates": quality_gates,
        "loops": loops,
    }


# ---------------------------------------------------------------------------
# Tool: scan_python_nodes
# ---------------------------------------------------------------------------


def scan_python_nodes_tool(scan_dir: str = "") -> str:
    """Scan Python node/tool files for error handling and shared patterns."""
    patterns = (
        [f"{scan_dir}/**/*.py"]
        if scan_dir and scan_dir != "None"
        else [
            "examples/**/nodes/*.py",
            "examples/**/tools/*.py",
            "projects/**/nodes/*.py",
        ]
    )

    findings: list[str] = []
    seen: set[str] = set()

    for pattern in patterns:
        for path_str in sorted(glob.glob(pattern, recursive=True)):
            real = str(Path(path_str).resolve())
            if real in seen:
                continue
            seen.add(real)

            try:
                content = Path(path_str).read_text(encoding="utf-8")
            except Exception:
                continue

            file_findings = _scan_python_file(path_str, content)
            if file_findings:
                findings.extend(file_findings)

    if not findings:
        return "No notable patterns found in Python nodes."

    return "# Python Node Scan\n\n" + "\n".join(findings)


def _scan_python_file(path: str, content: str) -> list[str]:
    """Check a single Python file for anti-patterns."""
    findings: list[str] = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Silent fallbacks
        if re.search(r"except\s*:", line) and "noqa" not in line:
            findings.append(f"  ⚠ {path}:{i} — bare except (silent fallback)")
        if re.search(r"\bor\s*\[\]", line):
            findings.append(f"  ⚠ {path}:{i} — `or []` fallback")
        if re.search(r"\bor\s*\{\}", line):
            findings.append(f"  ⚠ {path}:{i} — `or {{}}` fallback")

        # model_dump without to_serializable
        if "model_dump" in line and "to_serializable" not in content:
            findings.append(
                f"  📝 {path}:{i} — inline model_dump (candidate for to_serializable)"
            )

        # get_map_result reimplementation
        if (
            re.search(r"\.get\([\"']result[\"']\)", line)
            and "get_map_result" not in content
        ):
            findings.append(
                f"  📝 {path}:{i} — manual .get('result') (candidate for get_map_result)"
            )

    return findings


# ---------------------------------------------------------------------------
# Tool: count_patterns
# ---------------------------------------------------------------------------


def count_patterns_tool(scan_dir: str = "") -> str:
    """Count key patterns across all graph YAML files."""
    patterns = (
        [f"{scan_dir}/**/*.yaml"]
        if scan_dir and scan_dir != "None"
        else DEFAULT_SCAN_DIRS
    )

    counts = {
        "on_error: skip": 0,
        "on_error: retry": 0,
        "on_error: fail": 0,
        "on_error: fallback": 0,
        "type: map": 0,
        "type: agent": 0,
        "type: llm": 0,
        "type: python": 0,
        "type: router": 0,
        "quality_gate_nodes": 0,
        "total_graphs": 0,
        "total_nodes": 0,
    }

    seen: set[str] = set()

    for pattern in patterns:
        for path_str in sorted(glob.glob(pattern, recursive=True)):
            real = str(Path(path_str).resolve())
            if real in seen:
                continue
            seen.add(real)

            try:
                with open(path_str, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                if not isinstance(config, dict) or "nodes" not in config:
                    continue
            except Exception:
                continue

            counts["total_graphs"] += 1
            nodes = config.get("nodes", {})
            counts["total_nodes"] += len(nodes)

            for node_name, node_cfg in nodes.items():
                if not isinstance(node_cfg, dict):
                    continue

                ntype = node_cfg.get("type", "llm")
                type_key = f"type: {ntype}"
                if type_key in counts:
                    counts[type_key] += 1
                else:
                    counts[type_key] = 1

                on_error = node_cfg.get("on_error", "")
                if on_error:
                    err_key = f"on_error: {on_error}"
                    counts[err_key] = counts.get(err_key, 0) + 1

                # Quality gate detection
                name_lower = node_name.lower()
                if any(kw in name_lower for kw in QUALITY_KEYWORDS):
                    counts["quality_gate_nodes"] += 1

    lines = ["# Pattern Counts\n"]
    for key, val in sorted(counts.items()):
        lines.append(f"  {key}: {val}")

    return "\n".join(lines)
