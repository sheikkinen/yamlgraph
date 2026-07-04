"""Python function loader for type: python nodes.

This module enables YAML graphs to call arbitrary Python functions
by specifying the module path and function name, or a direct file path.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yamlgraph.tools.schema_loader_tool import (
    SchemaLoaderToolConfig,
    build_schema_loader_tool,
)
from yamlgraph.tools.write_data_file_tool import (
    WriteDataFileToolConfig,
    build_write_data_file_tool,
)
from yamlgraph.utils.guard_runtime import (
    GuardHaltError,
    enforce_post_guards,
    enforce_pre_guards,
    extract_guard_rules,
)

logger = logging.getLogger(__name__)


@dataclass
class PythonToolConfig:
    """Configuration for a Python tool.

    Attributes:
        module: Full module path (e.g., "examples.storyboard.nodes.image_node")
        path: File path to Python module. When ``graph_root`` is provided to
              loader callsites, relative paths resolve from that root and are
              confined within it. Mutually exclusive with ``module``.
        function: Function name within the module
        description: Human-readable description
    """

    function: str
    module: str | None = None
    path: str | None = None
    description: str = ""


def load_python_function(
    config: PythonToolConfig | SchemaLoaderToolConfig | WriteDataFileToolConfig,
    *,
    graph_root: Path | None = None,
    tool_name: str = "",
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
) -> Callable:
    """Load a Python function from module path or file path.

    Args:
        config: Python tool configuration or schema loader tool configuration
        graph_root: Graph root directory for graph-relative tool loading
        graph_path: Path to graph YAML file (for write_data_file self-mod guard)
        prompts_dir: Path to prompts directory (for write_data_file self-mod guard)

    Returns:
        The loaded function

    Raises:
        ValueError: If both path and module are set, or neither is set
        FileNotFoundError: If path does not point to an existing file
        ImportError: If module cannot be imported
        AttributeError: If function not found in module
    """
    if isinstance(config, WriteDataFileToolConfig):
        if graph_root is None:
            raise ValueError(
                "WriteDataFileToolConfig requires graph_root for path resolution"
            )
        return build_write_data_file_tool(
            tool_name or "write_data_file",
            config,
            graph_root=graph_root,
            graph_path=graph_path,
            prompts_dir=prompts_dir,
        )

    if isinstance(config, SchemaLoaderToolConfig):
        if graph_root is None:
            raise ValueError(
                "SchemaLoaderToolConfig requires graph_root for relative path resolution"
            )
        return build_schema_loader_tool(
            tool_name or "schema_loader",
            config,
            graph_root=graph_root,
        )

    if config.path and config.module:
        raise ValueError("PythonToolConfig: set 'path' or 'module', not both")
    if not config.path and not config.module:
        raise ValueError("PythonToolConfig: one of 'path' or 'module' is required")

    if config.path:
        resolved = _resolve_python_tool_path(
            config.path,
            graph_root=graph_root,
            tool_name=tool_name,
        )
        if not resolved.is_file():
            raise FileNotFoundError(f"Python tool path not found: {resolved}")
        spec = importlib.util.spec_from_file_location(resolved.stem, resolved)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        source_label = str(config.path)
    else:
        # Ensure current working directory is in path for project imports
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        try:
            mod = importlib.import_module(config.module)
        except ImportError as e:
            logger.error(f"Failed to import module: {config.module}")
            raise ImportError(f"Cannot import module '{config.module}': {e}") from e
        source_label = config.module

    try:
        func = getattr(mod, config.function)
    except AttributeError as e:
        logger.error(f"Function not found: {config.function} in {source_label}")
        raise AttributeError(
            f"Function '{config.function}' not found in '{source_label}'"
        ) from e

    if not callable(func):
        raise TypeError(f"'{config.function}' in '{source_label}' is not callable")

    logger.debug(f"Loaded Python function: {source_label}.{config.function}")
    return func


def _resolve_python_tool_path(
    path: str,
    *,
    graph_root: Path | None,
    tool_name: str,
) -> Path:
    candidate = Path(path)
    if graph_root is None:
        return candidate.resolve()

    root = graph_root.resolve()
    resolved = (
        candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    )
    try:
        resolved.relative_to(root)
    except ValueError:
        tool_label = f" '{tool_name}'" if tool_name else ""
        raise ValueError(
            f"Python tool{tool_label}: path '{path}' escapes graph root '{root}' "
            f"(resolved: {resolved})"
        ) from None
    return resolved


def parse_python_tools(tools_config: dict[str, Any]) -> dict[str, PythonToolConfig]:
    """Parse Python tools from YAML tools section.

    Only extracts tools with type: python.

    Args:
        tools_config: Dict from YAML tools: section

    Returns:
        Registry mapping tool names to PythonToolConfig objects
    """
    registry: dict[str, PythonToolConfig] = {}

    for name, config in tools_config.items():
        if config.get("type") != "python":
            continue

        has_module = "module" in config
        has_path = "path" in config
        has_function = "function" in config

        if not has_function or (not has_module and not has_path):
            logger.warning(
                f"Python tool '{name}' missing 'function' or 'module'/'path', skipping"
            )
            continue

        registry[name] = PythonToolConfig(
            module=config.get("module"),
            path=config.get("path"),
            function=config["function"],
            description=config.get("description", ""),
        )

    return registry


def create_python_node(
    node_name: str,
    node_config: dict[str, Any],
    python_tools: dict[str, PythonToolConfig | SchemaLoaderToolConfig],
    *,
    graph_root: Path | None = None,
) -> Callable[[dict[str, Any]], dict]:
    """Create a node that executes a Python function.

    The function receives the full state dict and should return
    a partial state update dict.

    Args:
        node_name: Name of the node in the graph
        node_config: Node configuration from YAML
        python_tools: Registry of available Python tools

    Returns:
        Node function that executes the Python function
    """
    tool_name = node_config.get("tool") or node_config.get("function")
    if not tool_name:
        raise ValueError(f"Python node '{node_name}' must specify 'tool' or 'function'")

    if tool_name not in python_tools:
        raise KeyError(f"Python tool '{tool_name}' not found in tools registry")

    tool_config = python_tools[tool_name]
    state_key = node_config.get("state_key", node_name)
    on_error = node_config.get("on_error", "fail")
    loop_limit = node_config.get("loop_limit")
    variable_templates = node_config.get("variables", {})
    guards_pre, guards_post = extract_guard_rules(node_config)

    # Load the function at node creation time
    func = load_python_function(
        tool_config,
        graph_root=graph_root,
        tool_name=tool_name,
    )

    def node_fn(state: dict[str, Any]) -> dict:
        """Execute the Python function and return state update."""
        # FR-027: Check loop limit (same pattern as LLM nodes)
        from yamlgraph.error_handlers import check_loop_limit

        loop_counts = dict(state.get("_loop_counts") or {})
        current_count = loop_counts.get(node_name, 0)

        if check_loop_limit(node_name, loop_limit, current_count):
            return {"_loop_limit_reached": True, "current_step": node_name}

        loop_counts[node_name] = current_count + 1

        # FR-677: pre-guards run before executing the function.
        if enforce_pre_guards(node_name, guards_pre, state):
            from yamlgraph.error_handlers import build_skip_error_state

            return build_skip_error_state(
                node_name=node_name,
                state_key=state_key,
                error_message=f"Python node '{node_name}' skipped by pre-guard",
                state=state,
            )

        logger.info(f"🐍 Executing Python node: {node_name} -> {tool_name}")

        # FR-252: Resolve variables expressions before calling function
        from yamlgraph.utils.expressions import resolve_node_variables

        resolved = resolve_node_variables(variable_templates, state)
        effective_state = {**state, **resolved} if resolved else state

        try:
            from yamlgraph.utils.expressions import resolve_node_variables

            if variable_templates:
                resolved = resolve_node_variables(variable_templates, state)
                effective_state = {**state, **resolved}
            else:
                effective_state = state

            result = func(effective_state)

            # FR-677: post-guards validate output; retry re-runs the function.
            result = enforce_post_guards(
                node_name,
                guards_post,
                state,
                result,
                execute=lambda: func(effective_state),
            )

            # If function returns a dict, merge with node metadata
            if isinstance(result, dict):
                result["current_step"] = node_name
                result["_loop_counts"] = loop_counts
                return result
            else:
                # Function returned a single value, store in state_key
                return {
                    state_key: result,
                    "current_step": node_name,
                    "_loop_counts": loop_counts,
                }

        except GuardHaltError:
            # FR-677: guard halts must surface even when on_error=skip.
            raise
        except Exception as e:
            logger.error(f"Python node {node_name} failed: {e}")

            if on_error == "skip":
                from yamlgraph.error_handlers import build_skip_error_state

                return build_skip_error_state(
                    node_name=node_name,
                    state_key=state_key,
                    error_message=str(e),
                    state=state,
                )
            else:
                raise

    node_fn.__name__ = f"{node_name}_python_node"
    return node_fn
