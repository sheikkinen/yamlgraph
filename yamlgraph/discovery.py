"""Shared graph discovery for protocol servers (MCP, A2A).

Extracted from mcp_server.py (Phase 0 of FR-208) so both MCP and A2A
servers share the same discovery logic.
"""

from __future__ import annotations

import glob
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default graph scan patterns (relative to project root)
DEFAULT_GRAPH_PATTERNS = [
    "examples/demos/*/*.yaml",
    "examples/*/*.yaml",
]


def discover_graphs(patterns: list[str]) -> list[dict[str, Any]]:
    """Scan directories for graph YAML files and parse headers.

    A YAML file is considered a graph if it contains a ``nodes`` key.
    This allows discovery of non-standard filenames (e.g. ``pipeline.yaml``,
    ``drill-down.yaml``) while excluding prompt templates.

    Args:
        patterns: Glob patterns to scan for YAML files.

    Returns:
        List of dicts with keys: name, description, path, required_vars.
    """
    graphs: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for pattern in patterns:
        for path_str in sorted(glob.glob(pattern, recursive=True)):
            real = str(Path(path_str).resolve())
            if real in seen_paths:
                continue
            seen_paths.add(real)

            try:
                with open(path_str) as f:
                    config = yaml.safe_load(f)
                if not isinstance(config, dict):
                    continue

                # Only include files that look like graphs (have nodes)
                if "nodes" not in config:
                    continue

                name = config.get("name", Path(path_str).parent.name)
                description = config.get("description", "")
                state = config.get("state", {})
                required_vars = list(state.keys()) if isinstance(state, dict) else []

                graphs.append(
                    {
                        "name": name,
                        "description": description,
                        "path": str(Path(path_str).resolve()),
                        "required_vars": required_vars,
                    }
                )
            except Exception:
                logger.warning("Failed to parse %s", path_str, exc_info=True)

    return graphs
