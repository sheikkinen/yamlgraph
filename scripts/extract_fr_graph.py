#!/usr/bin/env python3
"""FR-814: Extract knowledge graph from FR corpus.

Parses feature-requests/*.md, extracts typed edges between FRs based on
section context and keyword proximity, builds a causal DAG with transitive
closures, detects clusters, and outputs a deterministic YAML artifact.
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FR_DIR = Path("feature-requests")
OUTPUT_PATH = Path("reference/fr-knowledge-graph.yaml")
SCHEMA_VERSION = 2

FR_REF_RE = re.compile(r"\bFR-(\d+)\b")
SECTION_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)

# Noun extraction stopwords (local copy — R-3: no cross-import from hooks)
_NOUN_STOPWORDS = {
    "fix",
    "add",
    "support",
    "node",
    "nodes",
    "graph",
    "graphs",
    "yaml",
    "demo",
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "new",
    "test",
    "tests",
    "update",
    "improve",
    "refactor",
    "remove",
    "enable",
    "disable",
}
_FR_PREFIX = re.compile(r"^(fr|nc)-\d+-?", re.IGNORECASE)


def extract_filename_nouns(filename: str) -> list[str]:
    """Extract nouns from FR filename for cluster naming."""
    stem = Path(filename).stem
    stem = _FR_PREFIX.sub("", stem)
    tokens = [t.lower() for t in stem.split("-")]
    return [
        t for t in tokens if len(t) > 2 and not t.isdigit() and t not in _NOUN_STOPWORDS
    ]


# Edge typing rules (ordered by specificity)
CAUSAL_KEYWORDS = {
    "depends_on": [
        r"blocked\s+until",
        r"dependenc(?:y|ies)",
        r"depends\s+on",
        r"hard\s+activation\s+gate",
    ],
    "regression_of": [r"regression", r"introduced\s+(?:the\s+)?(?:this\s+)?regression"],
    "spawned_by": [r"seed\s+origin", r"parent\s+plan", r"spawned\s+by"],
    "substrate": [
        r"substrate",
        r"built\s+on(?:\s+top\s+of)?",
        r"consumes\s+contracts?\s+from",
    ],
    "supersedes": [r"supersedes", r"replaces"],
}

ASSOCIATIVE_SECTIONS = {
    "## Related",
    "## Prior art",
    "## Alternatives Considered",
}

# ---------------------------------------------------------------------------
# Metadata parsing
# ---------------------------------------------------------------------------


def parse_fr_id(filename: str) -> str | None:
    """Extract FR-XXX from filename."""
    m = re.match(r"(FR-\d+)", filename, re.IGNORECASE)
    return m.group(1).upper() if m else None


def parse_metadata(text: str) -> dict:
    """Extract front-matter metadata fields."""
    meta = {}
    for key in ("Status", "Priority", "Type", "Requested"):
        m = re.search(rf"^\*\*{key}:\*\*\s*(.+)$", text, re.MULTILINE)
        if m:
            val = m.group(1).strip()
            if key == "Status" or key == "Priority" or key == "Type":
                val = val.split()[0].lower()
            meta[key.lower()] = val
    return meta


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------


def get_sections(text: str) -> list[tuple[str, int, int]]:
    """Return list of (section_title, start_line, end_line)."""
    lines = text.splitlines()
    sections: list[tuple[str, int, int]] = []
    for i, line in enumerate(lines):
        m = re.match(r"^#{1,3}\s+(.+)$", line)
        if m:
            sections.append((m.group(1).strip(), i + 1, 0))
    # Fill end lines
    result = []
    for idx, (title, start, _) in enumerate(sections):
        end = sections[idx + 1][1] - 1 if idx + 1 < len(sections) else len(lines)
        result.append((title, start, end))
    return result


def section_at_line(sections: list[tuple[str, int, int]], line: int) -> str:
    """Find which section a line belongs to."""
    for title, start, end in sections:
        if start <= line <= end:
            return title
    return "(preamble)"


# ---------------------------------------------------------------------------
# Edge extraction
# ---------------------------------------------------------------------------


def extract_edges(source_id: str, text: str, lines: list[str]) -> list[dict]:
    """Extract all FR references and classify edges."""
    sections = get_sections(text)
    edges = []

    for i, line_text in enumerate(lines):
        line_num = i + 1
        for m in FR_REF_RE.finditer(line_text):
            target_id = f"FR-{m.group(1)}"
            if target_id == source_id:
                continue  # self-reference

            section_title = section_at_line(sections, line_num)
            edge_type, confidence, rule = classify_edge(
                line_text, section_title, m.start(), text, line_num
            )

            edges.append(
                {
                    "source": source_id,
                    "target": target_id,
                    "type": edge_type,
                    "causal": edge_type in CAUSAL_KEYWORDS,
                    "confidence": confidence,
                    "section": section_title,
                    "line": line_num,
                    "rule": rule,
                }
            )

    return edges


def classify_edge(
    line: str, section: str, ref_pos: int, full_text: str, line_num: int
) -> tuple[str, float, str]:
    """Classify an edge based on context. Returns (type, confidence, rule_id)."""
    # Check context window (80 chars around the reference)
    context_start = max(0, ref_pos - 80)
    context_end = min(len(line), ref_pos + 80)
    context = line[context_start:context_end].lower()

    # Inverse indicators: "prerequisite for FR-X" or "depends on this FR" means
    # FR-X depends on US, not us on them
    if re.search(r"prerequisite\s+for", context):
        return ("mentions", 0.5, "inverse_prerequisite")
    if re.search(r"depends\s+on\s+this", context):
        return ("mentions", 0.5, "inverse_depends_on_this")

    # Try causal keywords (highest priority)
    for edge_type, patterns in CAUSAL_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return (edge_type, 1.0, f"{edge_type}_keyword_exact")

    # Section-based heuristics for causal
    section_lower = section.lower()
    if "problem" in section_lower and re.search(
        r"regression|broke|crash|introduced", line, re.IGNORECASE
    ):
        return ("regression_of", 0.7, "regression_keyword_proximity")

    # Prior art section or markers
    if any(
        s.lower() in section_lower for s in ("related", "prior art", "alternatives")
    ):
        return ("prior_art", 1.0, "prior_art_section")

    if re.search(r"\*\*Prior\s+art:?\*\*", line, re.IGNORECASE):
        return ("prior_art", 1.0, "prior_art_marker")

    # First consumer referencing another FR
    if "first consumer" in section_lower or "first event" in line.lower():
        return ("first_consumer_of", 0.8, "first_consumer_section")

    # Default: mentions
    return ("mentions", 0.5, "unclassified_reference")


# ---------------------------------------------------------------------------
# DAG, closures, clusters
# ---------------------------------------------------------------------------


def build_causal_dag(edges: list[dict]) -> dict[str, set[str]]:
    """Build adjacency list from causal edges only."""
    dag: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        if e["causal"]:
            dag[e["source"]].add(e["target"])
    return dag


def detect_cycles(dag: dict[str, set[str]]) -> list[list[str]]:
    """Detect cycles using DFS. Returns list of cycle chains."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = defaultdict(int)
    cycles: list[list[str]] = []
    path: list[str] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in dag.get(node, set()):
            if color[neighbor] == GRAY:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    all_nodes = set(dag.keys())
    for e_targets in dag.values():
        all_nodes.update(e_targets)
    for node in sorted(all_nodes):
        if color[node] == WHITE:
            dfs(node)

    return cycles


def compute_closures(dag: dict[str, set[str]]) -> dict[str, list[str]]:
    """Compute transitive closure for each node (all reachable via causal edges)."""
    closures: dict[str, list[str]] = {}
    cache: dict[str, set[str]] = {}

    def reachable(node: str, visited: set[str] | None = None) -> set[str]:
        if node in cache:
            return cache[node]
        if visited is None:
            visited = set()
        if node in visited:
            return set()
        visited.add(node)
        result: set[str] = set()
        for dep in dag.get(node, set()):
            result.add(dep)
            result.update(reachable(dep, visited))
        cache[node] = result
        return result

    all_nodes = set(dag.keys())
    for e_targets in dag.values():
        all_nodes.update(e_targets)
    for node in sorted(all_nodes):
        deps = reachable(node)
        if deps:
            closures[node] = sorted(deps)

    return closures


def find_clusters(
    dag: dict[str, set[str]], all_nodes: set[str]
) -> dict[str, list[str]]:
    """Find connected components (ignoring edge direction)."""
    # Build undirected adjacency
    undirected: dict[str, set[str]] = defaultdict(set)
    for src, targets in dag.items():
        for tgt in targets:
            undirected[src].add(tgt)
            undirected[tgt].add(src)

    visited: set[str] = set()
    clusters: list[list[str]] = []

    for node in sorted(all_nodes):
        if node in visited or node not in undirected:
            continue
        # BFS
        component: list[str] = []
        queue = [node]
        while queue:
            n = queue.pop(0)
            if n in visited:
                continue
            visited.add(n)
            component.append(n)
            for neighbor in undirected.get(n, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        if len(component) >= 2:
            clusters.append(sorted(component))

    return {f"cluster-{i+1}": members for i, members in enumerate(clusters)}


def name_cluster(members: list[str], fr_file_map: dict[str, Path]) -> str:
    """FR-816: Derive semantic name from member filename nouns.

    Algorithm: count nouns across all member filenames, sort by
    descending count then lexical order, take top 3, join with hyphen.
    """
    from collections import Counter

    nouns: list[str] = []
    for fr_id in members:
        path = fr_file_map.get(fr_id)
        if path:
            nouns.extend(extract_filename_nouns(path.name))
    if not nouns:
        return "unnamed"
    counts = Counter(nouns)
    # Descending count, then lexical for ties
    top = [n for n, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:3]]
    return "-".join(top)


# ---------------------------------------------------------------------------
# Corpus fingerprint
# ---------------------------------------------------------------------------


def corpus_fingerprint(fr_files: list[Path]) -> str:
    """SHA-256 of sorted per-file content hashes."""
    hashes = []
    for f in sorted(fr_files):
        content = f.read_bytes()
        hashes.append(hashlib.sha256(content).hexdigest())
    combined = "\n".join(hashes).encode()
    return hashlib.sha256(combined).hexdigest()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def extract_graph(fr_dir: Path = FR_DIR) -> dict:
    """Run full extraction pipeline. Returns the graph dict."""
    fr_files = sorted(
        p for p in fr_dir.glob("*.md") if not p.name.endswith(".judgement.md")
    )

    nodes: dict[str, dict] = {}
    all_edges: list[dict] = []

    for fr_file in fr_files:
        fr_id = parse_fr_id(fr_file.name)
        if not fr_id:
            continue

        text = fr_file.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        meta = parse_metadata(text)
        nodes[fr_id] = meta

        edges = extract_edges(fr_id, text, lines)
        all_edges.extend(edges)

    # Deduplicate edges (keep highest confidence per source-target-type triple)
    edge_key_map: dict[tuple[str, str, str], dict] = {}
    for e in all_edges:
        key = (e["source"], e["target"], e["type"])
        if key not in edge_key_map or e["confidence"] > edge_key_map[key]["confidence"]:
            edge_key_map[key] = e
    unique_edges = sorted(
        edge_key_map.values(), key=lambda e: (e["source"], e["target"], e["type"])
    )

    # Build causal DAG
    dag = build_causal_dag(unique_edges)
    cycles = detect_cycles(dag)
    closures = compute_closures(dag)

    all_node_ids = set(nodes.keys())
    clusters = find_clusters(dag, all_node_ids)

    # FR-816: Build FR-ID → file path map for cluster naming
    fr_file_map: dict[str, Path] = {}
    for fr_file in fr_files:
        fr_id = parse_fr_id(fr_file.name)
        if fr_id:
            fr_file_map[fr_id] = fr_file

    # FR-816: Name clusters and produce v2 schema (object with name + members)
    used_names: set[str] = set()
    named_clusters: dict[str, dict] = {}
    for cluster_id, members in clusters.items():
        name = name_cluster(members, fr_file_map)
        # Collision resolution: append cluster numeric suffix
        if name in used_names:
            suffix = cluster_id.split("-")[-1]
            name = f"{name}-{suffix}"
        used_names.add(name)
        named_clusters[cluster_id] = {"name": name, "members": members}

    # Assign cluster IDs to nodes
    node_cluster_map: dict[str, str] = {}
    for cluster_id, cluster_data in named_clusters.items():
        for member in cluster_data["members"]:
            node_cluster_map[member] = cluster_id

    for fr_id, meta in nodes.items():
        if fr_id in node_cluster_map:
            meta["cluster"] = node_cluster_map[fr_id]

    # FR-817: Cross-cluster mentions (from deduplicated edge set)
    # Both endpoints must be in nodes AND have cluster assignments
    cross_cluster = [
        e
        for e in unique_edges
        if e["type"] == "mentions"
        and e["source"] in node_cluster_map
        and e["target"] in node_cluster_map
        and e["source"] in nodes
        and e["target"] in nodes
        and node_cluster_map[e["source"]] != node_cluster_map[e["target"]]
    ]
    cross_cluster.sort(key=lambda e: (e["source"], e["target"], e["line"]))

    fingerprint = corpus_fingerprint(fr_files)

    graph = {
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "corpus_fingerprint": f"sha256:{fingerprint}",
            "fr_count": len(nodes),
            "edge_count": len(unique_edges),
            "causal_edge_count": sum(1 for e in unique_edges if e["causal"]),
            "cluster_count": len(named_clusters),
        },
        "nodes": dict(sorted(nodes.items())),
        "edges": unique_edges,
        "closures": closures,
        "clusters": named_clusters,
        "cross_cluster_mentions": cross_cluster,
    }

    if cycles:
        graph["cycles"] = [{"chain": c} for c in cycles]

    return graph


def write_graph(graph: dict, output: Path = OUTPUT_PATH) -> None:
    """Write graph to YAML deterministically."""
    output.parent.mkdir(parents=True, exist_ok=True)

    # Exclude 'mentions' edges — weakest signal, dominates file size
    filtered_edges = [e for e in graph.get("edges", []) if e["type"] != "mentions"]

    # Compact edge keys
    compact_edges = []
    for e in filtered_edges:
        compact_edges.append(
            {
                "s": e["source"],
                "t": e["target"],
                "type": e["type"],
                "causal": e["causal"],
                "conf": e["confidence"],
                "ln": e["line"],
                "rule": e["rule"],
            }
        )

    output_graph = {
        "meta": {
            **graph["meta"],
            "edge_count": len(compact_edges),
            "mentions_excluded": graph["meta"]["edge_count"] - len(compact_edges),
        },
        "nodes": graph["nodes"],
        "edges": compact_edges,
        "closures": graph.get("closures", {}),
        "clusters": graph.get("clusters", {}),
    }

    # FR-817: Cross-cluster mentions (compact)
    cross_cluster = graph.get("cross_cluster_mentions", [])
    if cross_cluster:
        compact_cross = sorted(
            [
                {"s": e["source"], "t": e["target"], "ln": e["line"]}
                for e in cross_cluster
            ],
            key=lambda e: (e["s"], e["t"], e["ln"]),
        )
        output_graph["cross_cluster_mentions"] = {
            "count": len(compact_cross),
            "edges": compact_cross,
        }

    if "cycles" in graph:
        output_graph["cycles"] = graph["cycles"]

    content = yaml.dump(
        output_graph,
        Dumper=yaml.SafeDumper,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=200,
    )
    output.write_text(content, encoding="utf-8")


def check_staleness(fr_dir: Path = FR_DIR, output: Path = OUTPUT_PATH) -> bool:
    """Return True if the generated graph is current, False if stale."""
    if not output.exists():
        return False
    fr_files = sorted(
        p for p in fr_dir.glob("*.md") if not p.name.endswith(".judgement.md")
    )
    current_fp = corpus_fingerprint(fr_files)
    try:
        existing = yaml.safe_load(output.read_text(encoding="utf-8"))
        return existing["meta"]["corpus_fingerprint"] == f"sha256:{current_fp}"
    except (KeyError, TypeError, yaml.YAMLError):
        return False


def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract FR knowledge graph")
    parser.add_argument("--check", action="store_true", help="Check staleness only")
    parser.add_argument("--fr-dir", type=Path, default=FR_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    if args.check:
        if check_staleness(args.fr_dir, args.output):
            print("✓ FR knowledge graph is current")
            return 0
        else:
            print(
                "✗ FR knowledge graph is stale — run: python scripts/extract_fr_graph.py"
            )
            return 1

    graph = extract_graph(args.fr_dir)
    write_graph(graph, args.output)

    meta = graph["meta"]
    print(f"✓ FR knowledge graph generated: {args.output}")
    print(
        f"  {meta['fr_count']} FRs, {meta['edge_count']} edges "
        f"({meta['causal_edge_count']} causal), {meta['cluster_count']} clusters"
    )

    if "cycles" in graph:
        print(f"  ⚠ {len(graph['cycles'])} cycle(s) detected in causal edges:")
        for c in graph["cycles"]:
            print(f"    {' → '.join(c['chain'])}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
