#!/usr/bin/env python3
"""FR-1125: deterministic census of open-object schema paths on committed graphs.

An *open object* is a subschema with ``type: object`` and no declared
``properties`` — what the ``fields`` form produces for ``dict``,
``dict[str, Any]`` and ``list[dict]``, and what the ``output_schema`` form
produces for an object without ``properties``. Anthropic constrained decoding
reduces it to ``{"type": "object", "properties": {}, "additionalProperties":
false}``; the only instance is ``{}``.

The census walks every committed graph file, resolves each ``llm``/``router``
node's static provider exactly as the linter does, loads the node's prompt
schema, and lists every open-object path with its class:

- ``anthropic``   — statically Anthropic-bound: must be dispositioned (R-1)
- ``runtime``     — provider is a ``{state.x}`` reference: W029 stands
- ``other``       — statically another provider: listed, untouched

The ``PROVIDER`` environment variable is ignored on purpose so the ledger is
the same on every host; the built-in default (``anthropic``) applies when
neither the node nor ``defaults`` names a provider.

Usage:  python scripts/fr1125_open_object_census.py [--check docs/issues-2026-09-27-fr1125-census.md]
Writes the mechanical table to stdout (Markdown). ``--check`` exits 1 when the
committed ledger's mechanical section differs from the current tree.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROOTS = ("examples", "graphs", ".github")
BEGIN = "<!-- fr1125-census:begin -->"
END = "<!-- fr1125-census:end -->"


def _graph_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        base = ROOT / root
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.y*ml")):
            if "prompts" in p.parts or "node_modules" in p.parts:
                continue
            files.append(p)
    return files


def _load_graph(path: Path) -> dict | None:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("nodes"), dict):
        return None
    return doc


def open_objects(schema: dict) -> list[str]:
    """Canonical paths of concrete object subschemas with absent/empty properties.

    Mirrors the FR-1123 walker's traversal: ``$defs`` under ``$defs.<name>``,
    ``$ref`` is a stop, compositions branch, then ``properties`` / ``items``.
    """
    found: list[str] = []

    def walk(node: dict, path: list[str]) -> None:
        for name, sub in (node.get("$defs") or {}).items():
            walk(sub, [*path, "$defs", name])
        if "$ref" in node:
            return
        for keyword in ("anyOf", "oneOf", "allOf"):
            variants = node.get(keyword)
            if isinstance(variants, list):
                for i, variant in enumerate(variants):
                    walk(variant, [*path, f"{keyword}[{i}]"])
                return
        kind = node.get("type")
        if kind == "object":
            props = node.get("properties") or {}
            if not props:
                found.append(".".join(path) or "(root)")
                return
            for key, sub in props.items():
                walk(sub, [*path, key])
        elif kind == "array" and isinstance(node.get("items"), dict):
            walk(node["items"], [*path, "items"])

    walk(schema, [])
    return found


def _llm_nodes(nodes: dict) -> list[tuple[str, dict]]:
    """Top-level ``llm``/``router`` nodes plus map sub-nodes, named ``<map>/node``.

    A map's ``node:`` block is compiled through the same LLM factory and is
    Anthropic-bound under the same static resolution; FR-1073's census
    showed most repository LLM fan-out lives there. Race candidates and
    pipeline stages are outside this census and stated as such in the ledger.
    """
    out: list[tuple[str, dict]] = []
    for name, node in nodes.items():
        if not isinstance(node, dict):
            continue
        kind = node.get("type", "llm")
        if kind in ("llm", "router"):
            out.append((name, node))
        elif kind == "map" and isinstance(node.get("node"), dict):
            sub = node["node"]
            if sub.get("type", "llm") in ("llm", "router"):
                out.append((f"{name}/node", sub))
    return out


def census() -> list[dict[str, Any]]:
    from yamlgraph.linter.checks import get_prompt_path, resolve_prompts_dir
    from yamlgraph.schema_loader import load_schema_from_yaml
    from yamlgraph.utils.schema_walk import resolve_static_provider

    # Host-independent ledger: importing yamlgraph loads .env, which can set
    # PROVIDER (this host: deepseek). Neutralise it AFTER the import so a graph
    # that names no provider resolves to the built-in default, as on CI.
    os.environ.pop("PROVIDER", None)

    rows: list[dict[str, Any]] = []
    consumers: dict[str, set[str]] = {}
    for gpath in _graph_files():
        graph = _load_graph(gpath)
        if graph is None:
            continue
        rel_graph = gpath.relative_to(ROOT).as_posix()
        prompts_dir = resolve_prompts_dir(graph, gpath, gpath.parent)
        default_provider = (graph.get("defaults") or {}).get("provider")
        for node_name, node in _llm_nodes(graph["nodes"]):
            if node.get("parse_json"):
                continue
            prompt_name = node.get("prompt")
            if not prompt_name:
                continue
            prompt_path = get_prompt_path(prompt_name, prompts_dir)
            if prompt_path is None or not prompt_path.exists():
                continue
            rel_prompt = prompt_path.resolve().relative_to(ROOT).as_posix()
            consumers.setdefault(rel_prompt, set()).add(f"{rel_graph}#{node_name}")
            try:
                model = load_schema_from_yaml(prompt_path)
            except (
                Exception
            ) as exc:  # a malformed schema is its own defect, not this census's
                rows.append(
                    {
                        "graph": rel_graph,
                        "node": node_name,
                        "prompt": rel_prompt,
                        "path": f"(schema load failed: {type(exc).__name__})",
                        "provider": "?",
                        "class": "error",
                    }
                )
                continue
            if model is None:
                continue
            provider_value = node.get("provider")
            provider = resolve_static_provider(provider_value, default_provider)
            if provider is None:
                klass, shown = "runtime", str(provider_value or default_provider)
            elif provider == "anthropic":
                klass, shown = "anthropic", "anthropic"
            else:
                klass, shown = "other", provider
            for path in open_objects(model.model_json_schema()):
                rows.append(
                    {
                        "graph": rel_graph,
                        "node": node_name,
                        "prompt": rel_prompt,
                        "path": path,
                        "provider": shown,
                        "class": klass,
                    }
                )
    for row in rows:
        row["consumers"] = ", ".join(sorted(consumers.get(row["prompt"], set())))
    rows.sort(key=lambda r: (r["prompt"], r["path"], r["graph"], r["node"]))
    return rows


def render(rows: list[dict[str, Any]]) -> str:
    out = [
        BEGIN,
        "",
        "| # | prompt | schema path | graph#node | static provider | class | all consumers of the prompt |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        out.append(
            f"| {i} | `{r['prompt']}` | `{r['path']}` | `{r['graph']}#{r['node']}` | {r['provider']} | **{r['class']}** | {r['consumers']} |"
        )
    counts = {
        k: sum(1 for r in rows if r["class"] == k)
        for k in ("anthropic", "runtime", "other", "error")
    }
    out += [
        "",
        f"Rows: {len(rows)} — anthropic {counts['anthropic']}, runtime {counts['runtime']}, other {counts['other']}, error {counts['error']}. "
        f"Distinct prompt files: {len({r['prompt'] for r in rows})}.",
        "",
        END,
    ]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", type=Path, help="committed ledger to compare against")
    args = ap.parse_args()
    table = render(census())
    if args.check:
        text = args.check.read_text(encoding="utf-8").replace("\r\n", "\n")
        if BEGIN not in text or END not in text:
            print("ledger lacks census markers", file=sys.stderr)
            return 1
        committed = text[text.index(BEGIN) : text.index(END) + len(END)]
        if committed.strip() != table.strip():
            print("ledger differs from the current tree; regenerate", file=sys.stderr)
            return 1
        print("ledger matches the current tree")
        return 0
    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
