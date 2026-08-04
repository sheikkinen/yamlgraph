"""Tool manifests — declaration reuse over existing runtimes (FR-768).

A ``manifest:`` key in a ``tools:`` entry loads a typed manifest YAML and
translates it into the equivalent inline shell/python/graph tool
declaration at graph load. Translation only — the existing runtimes
execute the tool; no new execution engine.

Path semantics: the manifest path resolves relative to the referencing
graph; ``runtime`` paths inside a manifest resolve relative to the
manifest file (REQ-YG-574).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ShellRuntime(BaseModel):
    """``runtime.type: shell`` — same semantics as inline shell tools."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["shell"]
    command: str
    parse: Literal["text", "json", "none"] = "text"
    timeout: int = 30


class PythonRuntime(BaseModel):
    """``runtime.type: python`` — exactly one of ``path`` or ``module``."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["python"]
    function: str
    path: str | None = None
    module: str | None = None

    @model_validator(mode="after")
    def _exactly_one_source(self) -> PythonRuntime:
        if bool(self.path) == bool(self.module):
            raise ValueError(
                "python runtime requires exactly one of 'path' or 'module'"
            )
        return self


class GraphRuntime(BaseModel):
    """``runtime.type: graph`` — identical semantics to inline FR-658 tools."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["graph"]
    path: str
    input_mapping: dict[str, str] = Field(default_factory=dict)
    output_key: str = "result"


class ToolManifest(BaseModel):
    """Typed manifest contract, validated at the graph-load boundary."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    runtime: ShellRuntime | PythonRuntime | GraphRuntime = Field(discriminator="type")


def _fail(tool_name: str, manifest_ref: str, reason: str) -> ValueError:
    return ValueError(
        f"Tool '{tool_name}': manifest '{manifest_ref}' invalid: {reason}"
    )


def _translate(manifest: ToolManifest, manifest_dir: Path) -> dict[str, Any]:
    """Translate a validated manifest into the inline declaration shape."""
    rt = manifest.runtime
    if isinstance(rt, ShellRuntime):
        return {
            "type": "shell",
            "command": rt.command,
            "description": manifest.description,
            "parse": rt.parse,
            "timeout": rt.timeout,
        }
    if isinstance(rt, PythonRuntime):
        translated: dict[str, Any] = {
            "type": "python",
            "function": rt.function,
            "description": manifest.description,
        }
        if rt.path is not None:
            translated["path"] = str((manifest_dir / rt.path).resolve())
        else:
            translated["module"] = rt.module
        return translated
    # GraphRuntime
    graph_path = Path(rt.path)
    if not graph_path.is_absolute():
        graph_path = (manifest_dir / graph_path).resolve()
    return {
        "type": "graph",
        "path": str(graph_path),
        "description": manifest.description,
        "input_mapping": rt.input_mapping,
        "output_key": rt.output_key,
    }


def expand_tool_manifests(
    tools: dict[str, Any], source_path: Path | None
) -> dict[str, Any]:
    """Expand ``manifest:`` tool entries into inline declarations.

    Entries without a ``manifest`` key pass through unchanged (AC-08).

    Args:
        tools: Raw ``tools:`` section from graph YAML.
        source_path: Path of the referencing graph file, for
            graph-relative manifest resolution.

    Returns:
        Tools dict with every manifest entry replaced by its translation.

    Raises:
        ValueError: On any missing, unparseable, or invalid manifest —
            at graph load, never at invocation.
    """
    if not tools:
        return tools

    graph_dir = source_path.parent if source_path else Path.cwd()
    expanded: dict[str, Any] = {}
    for name, entry in tools.items():
        if not isinstance(entry, dict) or "manifest" not in entry:
            expanded[name] = entry
            continue

        manifest_ref = str(entry["manifest"])
        extra_keys = sorted(set(entry) - {"manifest"})
        if extra_keys:
            raise _fail(
                name,
                manifest_ref,
                f"a manifest entry allows only the 'manifest' key, "
                f"found extra keys: {', '.join(extra_keys)}",
            )

        manifest_path = Path(manifest_ref)
        if not manifest_path.is_absolute():
            manifest_path = (graph_dir / manifest_path).resolve()
        if not manifest_path.is_file():
            raise _fail(name, manifest_ref, f"file not found: {manifest_path}")

        try:
            raw = yaml.safe_load(manifest_path.read_text())
        except yaml.YAMLError as e:
            raise _fail(name, manifest_ref, f"YAML parse error: {e}") from e
        if not isinstance(raw, dict):
            raise _fail(name, manifest_ref, "manifest must be a YAML mapping")

        try:
            manifest = ToolManifest.model_validate(raw)
        except ValidationError as e:
            raise _fail(name, manifest_ref, str(e)) from e

        if manifest.name != name:
            raise _fail(
                name,
                manifest_ref,
                f"manifest name '{manifest.name}' does not match tool key '{name}'",
            )

        expanded[name] = _translate(manifest, manifest_path.parent)

    return expanded
