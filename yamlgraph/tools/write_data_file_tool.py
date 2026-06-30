"""Built-in write_data_file tool (`type: write_data_file`).

Writes structured data (dict/list) to a YAML file within the graph workspace.
Symmetric counterpart to the `data_files` read directive.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WriteDataFileToolConfig:
    """Configuration for write_data_file tools."""

    state_key: str


def parse_write_data_file_tools(
    tools_config: dict[str, Any],
) -> dict[str, WriteDataFileToolConfig]:
    """Parse write_data_file tools from YAML tools section."""
    registry: dict[str, WriteDataFileToolConfig] = {}

    for name, raw_config in tools_config.items():
        if (
            not isinstance(raw_config, dict)
            or raw_config.get("type") != "write_data_file"
        ):
            continue

        state_key = raw_config.get("state_key")
        if not isinstance(state_key, str) or not state_key:
            raise ValueError(
                f"write_data_file tool '{name}' must define non-empty string 'state_key'"
            )

        registry[name] = WriteDataFileToolConfig(state_key=state_key)

    return registry


_VALID_EXTENSIONS = {".yaml", ".yml"}


def build_write_data_file_tool(
    name: str,
    config: WriteDataFileToolConfig,
    *,
    graph_root: Path,
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
) -> Callable[[dict[str, Any] | None], dict[str, Any]]:
    """Build a callable write_data_file tool with compile-time closure.

    Args:
        name: Tool name for error messages
        config: Tool configuration
        graph_root: Graph root directory (paths resolved relative to this)
        graph_path: Path to the graph YAML file (self-modification guard)
        prompts_dir: Path to prompts directory (self-modification guard)

    Returns:
        Callable that accepts state dict with 'path' and 'data' keys
    """
    # Resolve protected paths at compile time (closure captures these)
    resolved_graph_path = graph_path.resolve() if graph_path else None
    resolved_prompts_dir = prompts_dir.resolve() if prompts_dir else None
    resolved_root = graph_root.resolve()

    def _write(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        effective_state = state if isinstance(state, dict) else kwargs

        rel_path = effective_state.get("path")
        data = effective_state.get("data")

        if not isinstance(rel_path, str) or not rel_path:
            raise ValueError(
                f"write_data_file tool '{name}': 'path' must be a non-empty string"
            )

        if data is None:
            raise ValueError(f"write_data_file tool '{name}': 'data' must not be None")

        # Reject absolute paths
        if Path(rel_path).is_absolute():
            raise ValueError(
                f"write_data_file tool '{name}': absolute paths are not allowed: "
                f"'{rel_path}'"
            )

        # Resolve and validate containment
        target = (resolved_root / rel_path).resolve()
        try:
            target.relative_to(resolved_root)
        except ValueError:
            raise ValueError(
                f"write_data_file tool '{name}': path '{rel_path}' escapes graph "
                f"directory '{resolved_root}'"
            ) from None

        # Extension check (v1: YAML only)
        ext = target.suffix.lower()
        if ext not in _VALID_EXTENSIONS:
            raise ValueError(
                f"write_data_file tool '{name}': unsupported extension '{ext}'. "
                f"Only YAML extensions are supported: {sorted(_VALID_EXTENSIONS)}"
            )

        # Self-modification guard
        if resolved_graph_path and target == resolved_graph_path:
            raise ValueError(
                f"write_data_file tool '{name}': self-modification not allowed — "
                f"cannot write to graph file '{rel_path}'"
            )
        if resolved_prompts_dir:
            try:
                target.relative_to(resolved_prompts_dir)
                raise ValueError(
                    f"write_data_file tool '{name}': self-modification not allowed — "
                    f"cannot write to prompts directory '{rel_path}'"
                )
            except ValueError as e:
                if "self-modification" in str(e):
                    raise

        # Create parent directories
        target.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: tempfile in same directory, then os.replace
        fd, tmp_path = tempfile.mkstemp(
            dir=target.parent, suffix=".tmp", prefix=".write_data_file_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            os.replace(tmp_path, target)
        except BaseException:
            # Clean up temp file on any failure
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise

        return {config.state_key: str(target)}

    return _write
