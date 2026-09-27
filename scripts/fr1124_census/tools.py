"""FR-1124 census slot adapters for examples/demos/corpus_census.

discover: one identity ``<graph>::<node>`` per inventory row, sliced by
``source`` = ``"<start>:<stop>"`` (the census map caps at 200 items).
extract: a dossier for one identity — the node, its deterministic
downstream readers and outgoing edges, and the full graph text.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[2]
MAX_GRAPH_CHARS = 12000


def discover(state: dict[str, Any]) -> list[str]:
    sys.path.insert(0, str(REPO / "scripts"))
    from fr1124_inventory import inventory

    start, stop = (int(x) for x in str(state["source"]).split(":"))
    items = [f"{g}::{n}" for g, n, _ in inventory(REPO)][start:stop]
    if not items:
        raise ValueError(f"empty inventory slice: {state['source']}")
    return items


def _edges_from(doc: dict, node: str) -> list[str]:
    out = []
    for e in doc.get("edges") or []:
        if not isinstance(e, dict):
            continue
        src = e.get("from")
        if src == node or (isinstance(src, list) and node in src):
            to = e.get("to") or e.get("targets") or e.get("routes")
            out.append(f"{e.get('condition', '')} -> {to}".strip())
    return out


def _readers(doc: dict, node: str, key: str) -> list[str]:
    pat = re.compile(rf"(state\.{re.escape(key)}\b|\b{re.escape(key)}\b)")
    readers = []
    for name, cfg in (doc.get("nodes") or {}).items():
        if name == node:
            continue
        if pat.search(yaml.safe_dump(cfg, sort_keys=False)):
            readers.append(str(name))
    return readers


def extract(state: dict[str, Any]) -> str:
    graph, node = str(state["item"]).split("::", 1)
    text = (REPO / graph).read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    cfg = doc["nodes"][node]
    key = str(cfg.get("state_key", node))
    return "\n".join(
        [
            f"GRAPH: {graph}",
            f"NODE: {node}",
            f"STATE_KEY: {key}",
            f"NODE_CONFIG:\n{yaml.safe_dump(cfg, sort_keys=False)}",
            f"EDGES_OUT: {_edges_from(doc, node) or 'none'}",
            f"NODES_REFERENCING_STATE_KEY: {_readers(doc, node, key) or 'none'}",
            "FULL_GRAPH_YAML:",
            text[:MAX_GRAPH_CHARS],
        ]
    )
