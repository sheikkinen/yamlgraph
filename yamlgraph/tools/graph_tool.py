"""Graph-as-Tool: invoke a YAMLGraph pipeline in-process as a callable tool.

FR-658: Adds ``type: graph`` tool type. An agent or tool_call node can
invoke a full graph pipeline without knowing it is one — it sees a typed
tool with input schema and text output.

This module stays in Layer 3 (Side Effects). It receives pre-compiled
graph objects from the caller in Layer 2 (``graph_loader._parse_all_tools``).

AC-3:  StructuredTool schema from ``input_mapping`` keys.
AC-4:  Circular-ref guard at **invocation** time via ``_loading_stack``.
AC-9:  Pipeline errors caught → error text, never crash caller.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def make_graph_tool_fn(
    compiled: Any,
    input_mapping: dict[str, str],
    output_key: str,
    graph_path: Path,
    loading_stack: ContextVar[list[Path]],
    default_variables: dict[str, Any] | None = None,
) -> Callable[..., str]:
    """Create a callable that invokes a pre-compiled graph as a tool.

    AC-4: Checks ``loading_stack`` at invocation time for circular refs.
    AC-8: Uses pre-compiled graph (compilation happened at parse time).
    AC-9: Catches exceptions, returns error text.

    Args:
        compiled: Pre-compiled LangGraph (``sg.compile()`` result).
        input_mapping: Maps tool kwarg names → graph variable names.
        output_key: State key to extract from result.
        graph_path: Resolved path to child graph YAML (for cycle detection).
        loading_stack: ContextVar from subgraph_nodes for circular ref guard.
        default_variables: Graph-level variables from child config (injected as defaults).

    Returns:
        Callable(**kwargs) → str
    """

    def tool_fn(**kwargs: Any) -> str:
        # AC-4: circular reference guard at invocation time
        stack = loading_stack.get([])
        if graph_path in stack:
            cycle = " -> ".join(str(p) for p in [*stack, graph_path])
            return f"Error: Circular graph-tool reference: {cycle}"
        token = loading_stack.set([*stack, graph_path])
        try:
            # Map tool kwargs → graph variables via input_mapping
            # Default variables from child graph YAML are injected first,
            # then tool kwargs override (so entity_type etc. are always set)
            variables = dict(default_variables or {})
            variables.update({input_mapping.get(k, k): v for k, v in kwargs.items()})
            result = compiled.invoke(variables)
            value = result.get(output_key, result)
            # FR-810: dict/list outputs serialize as JSON (parseable by
            # parsed_key), not Python repr — normalize at the boundary
            if isinstance(value, dict | list):
                return json.dumps(value, default=str)
            return str(value)
        except Exception as e:
            # AC-9: surface error text, don't crash parent
            return f"Error: {e}"
        finally:
            loading_stack.reset(token)

    return tool_fn


def build_graph_tool(
    name: str,
    config: dict[str, Any],
    callable_fn: Callable[..., str],
) -> Any:
    """Wrap a graph-tool callable as a LangChain StructuredTool.

    AC-3: Schema generated from ``input_mapping`` keys — each key
    becomes a ``str``-typed field in a dynamic Pydantic ArgsModel.

    Args:
        name: Tool name for the LLM.
        config: Graph tool config dict with ``description``, ``input_mapping``.
        callable_fn: The callable produced by ``make_graph_tool_fn``.

    Returns:
        LangChain ``StructuredTool`` instance.
    """
    from langchain_core.tools import StructuredTool
    from pydantic import Field, create_model

    input_mapping = config.get("input_mapping", {})
    description = config.get("description", name)

    # Build args schema from input_mapping keys
    if input_mapping:
        fields = {
            key: (str, Field(description=f"Input: {key}")) for key in input_mapping
        }
        ArgsModel = create_model(f"{name}_args", **fields)
    else:
        ArgsModel = None

    return StructuredTool.from_function(
        func=callable_fn,
        name=name,
        description=description,
        args_schema=ArgsModel,
    )
