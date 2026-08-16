"""Content identity for an executable graph artifact (FR-807)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from yamlgraph.config import PROMPTS_DIR


def compute_artifact_hash(graph_path: str | Path) -> str:
    """Hash a canonical manifest of the graph and its resolved prompt files."""
    graph_path = Path(graph_path).resolve()
    root = graph_path.parent
    artifacts: set[Path] = set()
    _collect_graph_artifacts(graph_path, artifacts)

    manifest = [
        {
            "path": _manifest_path(path, root),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(artifacts, key=lambda item: item.as_posix())
    ]
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _collect_graph_artifacts(graph_path: Path, artifacts: set[Path]) -> None:
    graph_path = graph_path.resolve()
    if graph_path in artifacts:
        return
    if not graph_path.is_file():
        raise ValueError(f"Cannot hash executable artifact: missing graph {graph_path}")
    artifacts.add(graph_path)
    config = yaml.safe_load(graph_path.read_text(encoding="utf-8")) or {}
    prompts_dir = config.get("prompts_dir") or (config.get("defaults") or {}).get(
        "prompts_dir"
    )
    prompts_relative = config.get("prompts_relative", False)

    _collect_node_artifacts(
        config.get("nodes") or {},
        graph_path,
        prompts_dir,
        prompts_relative,
        artifacts,
    )
    _collect_tool_artifacts(config.get("tools") or {}, graph_path, artifacts)


def _collect_node_artifacts(
    nodes: dict,
    graph_path: Path,
    prompts_dir: str | None,
    prompts_relative: bool,
    artifacts: set[Path],
) -> None:
    """Collect prompt and child-graph files referenced by graph nodes."""
    for node in nodes.values():
        if not isinstance(node, dict):
            continue
        if node.get("type") == "subgraph":
            child = node.get("graph") or node.get("path")
            if child:
                _collect_graph_artifacts(graph_path.parent / str(child), artifacts)
        prompt = node.get("prompt")
        if prompt:
            artifacts.add(
                _resolved_prompt_or_error(
                    str(prompt), graph_path, prompts_dir, prompts_relative
                )
            )


def _resolved_prompt_or_error(
    prompt: str, graph_path: Path, prompts_dir: str | None, prompts_relative: bool
) -> Path:
    try:
        return _resolve_graph_prompt(prompt, graph_path, prompts_dir, prompts_relative)
    except FileNotFoundError as exc:
        raise ValueError(
            f"Cannot hash executable artifact: unresolved prompt '{prompt}' "
            f"referenced by {graph_path}"
        ) from exc


def _collect_tool_artifacts(
    tools: dict, graph_path: Path, artifacts: set[Path]
) -> None:
    """Collect graph-tool manifests and their executable child graphs."""
    for tool in tools.values():
        if not isinstance(tool, dict):
            continue
        manifest_ref = tool.get("manifest")
        declaration = tool
        declaration_root = graph_path.parent
        if manifest_ref:
            manifest = (graph_path.parent / str(manifest_ref)).resolve()
            if not manifest.is_file():
                raise ValueError(
                    f"Cannot hash executable artifact: missing tool manifest {manifest}"
                )
            artifacts.add(manifest)
            declaration = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            declaration_root = manifest.parent
        runtime = declaration.get("runtime", declaration)
        if runtime.get("type") == "graph" and runtime.get("path"):
            _collect_graph_artifacts(declaration_root / str(runtime["path"]), artifacts)


def _resolve_graph_prompt(
    prompt: str, graph_path: Path, prompts_dir: str | None, prompts_relative: bool
) -> Path:
    filename = Path(prompt)
    if filename.suffix not in {".yaml", ".yml"}:
        filename = filename.with_suffix(".yaml")
    candidates = []
    if prompts_relative:
        candidates.append(graph_path.parent / (prompts_dir or "") / filename)
    elif prompts_dir:
        candidates.append(Path(prompts_dir) / filename)
    candidates.extend([graph_path.parent / filename, PROMPTS_DIR / filename])
    parts = prompt.rsplit("/", 1)
    if len(parts) == 2:
        candidates.append(Path(parts[0]) / "prompts" / filename.name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(prompt)


def _manifest_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = ["compute_artifact_hash"]
