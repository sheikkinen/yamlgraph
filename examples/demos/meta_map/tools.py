"""FR-1113 meta-map demo — Python tools.

The LLM claims which map nodes a file has; `reconcile_claim` grades that
claim against `parse_map_nodes`, the same parse discovery selects with.
Poisoned inputs are read plainly and reach the LLM unfiltered.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from yamlgraph.models.map_results import MapFailure, MapVerdict

DEFAULT_SCAN_ROOTS = ["examples", "graphs"]
DEFAULT_OUTPUT_PATH = "outputs/meta_map/report.md"

# Checked in order; the first rule a node matches is its version.
VERSION_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("overflow", ("on_overflow",)),
    ("result-contract", ("failures", "min_success")),
    ("timeout", ("timeout",)),
    ("capped", ("max_items",)),
]
VERSION_ORDER = ["core", "capped", "timeout", "result-contract", "overflow"]


class SourceText(BaseModel):
    path: str
    text: str


class MapClaim(BaseModel):
    map_nodes: list[str]
    intent: str
    map_role: str


class MapNodeRecord(BaseModel):
    name: str
    sub_node_type: str
    declared_keys: list[str]
    version: str


class GraphRecord(BaseModel):
    path: str
    graph_version: str
    map_nodes: list[MapNodeRecord]
    intent: str
    map_role: str


class ClaimMismatchError(ValueError):
    """The LLM's claimed map nodes contradict the parse of the source."""


def parse_map_nodes(text: str) -> dict[str, dict]:
    """Return top-level `type: map` nodes by name; raises yaml.YAMLError."""
    doc = yaml.safe_load(text)
    nodes = doc.get("nodes") if isinstance(doc, dict) else None
    if not isinstance(nodes, dict):
        return {}
    return {
        name: cfg
        for name, cfg in nodes.items()
        if isinstance(cfg, dict) and cfg.get("type") == "map"
    }


def classify_map_version(cfg: dict) -> str:
    for version, keys in VERSION_RULES:
        if any(key in cfg for key in keys):
            return version
    return "core"


def discover_map_graphs(state: dict) -> dict:
    roots = state.get("scan_roots") or DEFAULT_SCAN_ROOTS
    paths: list[str] = []
    for root in roots:
        for path in sorted(Path(root).rglob("*")):
            if path.suffix not in (".yaml", ".yml") or not path.is_file():
                continue
            try:
                found = parse_map_nodes(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                raise ValueError(f"Malformed YAML in {path.as_posix()}: {e}") from e
            if found:
                paths.append(path.as_posix())
    return {"paths": paths}


def poison_the_source(state: dict) -> dict:
    poison = list(state["poison"]["paths"])
    for path in poison:
        if not Path(path).is_file():
            raise FileNotFoundError(f"Poison path does not exist: {path}")
    return {"paths": list(state["paths"]) + poison}


def read_source(state: dict) -> dict:
    path = state["path"]
    text = Path(path).read_bytes().decode("utf-8")
    return {"source": SourceText(path=path, text=text)}


def _as_model(model: type[BaseModel], value: Any) -> Any:
    if isinstance(value, model):
        return value
    if isinstance(value, BaseModel):
        value = value.model_dump()
    return model.model_validate(value)


def reconcile_claim(state: dict) -> dict:
    source = _as_model(SourceText, state["source"])
    claim = _as_model(MapClaim, state["claim"])
    try:
        parsed = parse_map_nodes(source.text)
    except yaml.YAMLError:
        parsed = {}
    claimed = sorted(set(claim.map_nodes))
    if not parsed or claimed != sorted(parsed):
        reason = " (source has no map nodes)" if not parsed else ""
        raise ClaimMismatchError(
            f"{source.path}: claimed {sorted(claim.map_nodes)}, "
            f"parsed {sorted(parsed)}{reason}"
        )
    nodes = [
        MapNodeRecord(
            name=name,
            sub_node_type=str((cfg.get("node") or {}).get("type", "llm")),
            declared_keys=[key for key in cfg if key != "type"],
            version=classify_map_version(cfg),
        )
        for name, cfg in parsed.items()
    ]
    record = GraphRecord(
        path=source.path,
        graph_version=max((n.version for n in nodes), key=VERSION_ORDER.index),
        map_nodes=nodes,
        intent=claim.intent,
        map_role=claim.map_role,
    )
    return {"graph_record": record}


def _merged(state: dict) -> dict:
    """FR-1116: the memo merge result — the whole current population."""
    return state["merged"]["result"]


def _records(state: dict) -> list[tuple[int, GraphRecord]]:
    rows = []
    for item in _merged(state)["records"]:
        data = dict(item)
        index = data.pop("_map_index")
        rows.append((index, GraphRecord.model_validate(data)))
    return sorted(rows, key=lambda row: row[0])


def _failures(state: dict) -> list[MapFailure]:
    failures = [_as_model(MapFailure, f) for f in _merged(state)["failures"]]
    return sorted(failures, key=lambda f: f.index)


def _verdict(state: dict) -> MapVerdict:
    return _as_model(MapVerdict, _merged(state)["verdict"])


def reduce_inputs(state: dict) -> dict:
    verdict = _verdict(state)
    records = [record for _, record in _records(state)]
    counts = {
        "dispatched": verdict.dispatched,
        "succeeded": verdict.succeeded,
        "tolerated": verdict.tolerated,
        "failed": verdict.failed,
        "by_version": dict(Counter(r.graph_version for r in records)),
    }
    return {
        "reduce_input": {
            "records": [r.model_dump() for r in records],
            "counts": counts,
        }
    }


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_report(state: dict) -> dict:
    verdict = _verdict(state)
    paths = list(state["paths"])
    records = _records(state)
    failures = _failures(state)

    seen = [index for index, _ in records] + [f.index for f in failures]
    if sorted(seen) != list(range(len(paths))):
        raise ValueError(
            f"Report must account each dispatch index 0..{len(paths) - 1} once; "
            f"got {sorted(seen)}"
        )

    required = verdict.min_success
    status = "met" if verdict.met else "unmet"
    memo = _merged(state)["counts"]
    lines = [
        f"# Map usage in YAMLGraph — {len(paths)} paths",
        "",
        f"Coverage: {verdict.dispatched} dispatched · {verdict.succeeded} succeeded"
        f" · {verdict.tolerated} tolerated · {verdict.failed} failed"
        f" (min_success {required}, {status})",
        "",
        f"Memo: {memo['executed_ok']} executed ok · {memo['executed_failed']}"
        f" executed failed · {memo['reused_ok']} reused ok"
        f" · {memo['reused_failed']} reused failed",
        "",
        "Map version = declared YAML keys; the runtime applies the FR-1073 "
        "result contract to every map.",
        "",
        "| Path | Map nodes | Sub-node | Version | Declared keys | Intent |",
        "|------|-----------|----------|---------|---------------|--------|",
    ]
    for _, record in records:
        nodes = record.map_nodes
        lines.append(
            "| "
            + " | ".join(
                [
                    record.path,
                    "; ".join(n.name for n in nodes),
                    "; ".join(n.sub_node_type for n in nodes),
                    record.graph_version,
                    "; ".join(", ".join(n.declared_keys) for n in nodes),
                    _cell(record.intent),
                ]
            )
            + " |"
        )
    lines += ["", "## Summary", "", str(state.get("overall") or ""), ""]
    lines += [
        "## Failures",
        "",
        "| Index | Path | Error type | Detail (`MapFailure.message`) |",
        "|-------|------|------------|-------------------------------|",
    ]
    for failure in failures:
        lines.append(
            f"| {failure.index} | {paths[failure.index]} | {failure.error_type}"
            f" | {_cell(failure.message)} |"
        )

    output = Path(state.get("output_path") or DEFAULT_OUTPUT_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"report_path": str(output)}
