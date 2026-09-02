#!/usr/bin/env python3
"""FR-636 Phase 1: Verify every NodeType has at least one demo that uses it.

Cross-references yamlgraph.constants.NodeType enum members against
examples/demos/*/graph.yaml node type declarations.

Exit code:
  0 — all node types covered (or explicitly allowlisted)
  1 — one or more node types have zero demo coverage

Usage:
    python scripts/node_type_coverage.py
    python scripts/node_type_coverage.py --strict  # fail on allowlisted too
"""

import sys
from pathlib import Path

# Resolve project root (script lives in scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMOS_DIR = PROJECT_ROOT / "examples" / "demos"

# Types that require external runtime and cannot run in standard demo environment.
# Empty if all types can be demonstrated — keep this minimal.
ALLOWLIST: frozenset[str] = frozenset()


def get_node_types() -> set[str]:
    """Load NodeType enum values from constants module."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from yamlgraph.constants import NodeType

    return {member.value for member in NodeType}


def scan_demos() -> dict[str, list[str]]:
    """Scan demo graph.yaml files for node type usage.

    Returns:
        Dict mapping node_type -> list of demo names that use it.
    """
    import yaml

    type_to_demos: dict[str, list[str]] = {}

    # Scan top-level graph.yaml and subgraph directories
    for graph_file in sorted(DEMOS_DIR.glob("**/graph.yaml")) + sorted(
        DEMOS_DIR.glob("**/*.yaml")
    ):
        # Deduplicate: glob("**/*.yaml") covers graph.yaml too
        if graph_file.suffix != ".yaml":
            continue
        # Skip prompt YAML files
        if "prompts" in graph_file.parts:
            continue

        # Demo name = first directory under demos/
        rel = graph_file.relative_to(DEMOS_DIR)
        demo_name = rel.parts[0]

        try:
            content = yaml.safe_load(graph_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: S112 — skip unparseable YAML silently
            continue

        if not content or "nodes" not in content:
            continue

        nodes = content["nodes"]
        if not isinstance(nodes, dict):
            continue

        for _node_name, node_config in nodes.items():
            if not isinstance(node_config, dict):
                continue
            node_type = node_config.get("type", "llm")
            type_to_demos.setdefault(node_type, []).append(demo_name)

    return type_to_demos


def main() -> int:
    strict = "--strict" in sys.argv

    node_types = get_node_types()
    demo_coverage = scan_demos()

    covered = []
    allowlisted = []
    missing = []

    for nt in sorted(node_types):
        demos = demo_coverage.get(nt, [])
        unique_demos = sorted(set(demos))
        if unique_demos:
            covered.append((nt, unique_demos))
        elif nt in ALLOWLIST and not strict:
            allowlisted.append(nt)
        else:
            missing.append(nt)

    # Report
    print(f"NodeType enum: {len(node_types)} members")
    print(f"Covered by demos: {len(covered)}")
    if allowlisted:
        print(f"Allowlisted (integration-only): {len(allowlisted)}")
    print()

    for nt, demos in covered:
        print(
            f"  ✓ {nt:<20} ({len(demos)} demos: {', '.join(demos[:3])}{'...' if len(demos) > 3 else ''})"
        )

    if allowlisted:
        print()
        for nt in allowlisted:
            print(f"  ⊘ {nt:<20} (allowlisted — requires external runtime)")

    if missing:
        print()
        print("❌ Node types with ZERO demo coverage:")
        for nt in missing:
            print(f"  ✗ {nt:<20} — needs a demo or deletion")
        print()
        return 1

    print()
    print("✅ All node types covered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
