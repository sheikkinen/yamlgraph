"""LangChain tool builders for shell and Python tool configs.

Extracted from agent.py to keep module size within limits.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import Field, create_model

from yamlgraph.tools.python_tool import PythonToolConfig, load_python_function
from yamlgraph.tools.schema_loader_tool import SchemaLoaderToolConfig
from yamlgraph.tools.shell import ShellToolConfig, execute_shell_tool


def build_langchain_tool(name: str, config: ShellToolConfig) -> Callable:
    """Convert shell config to LangChain Tool.

    Args:
        name: Tool name for LLM to reference
        config: Shell tool configuration

    Returns:
        LangChain-compatible tool function
    """
    # Extract variable names from command template
    var_names = re.findall(r"\{(\w+)\}", config.command)

    # Create dynamic Pydantic model for tool args
    if var_names:
        fields = {
            var: (str, Field(description=f"Value for {var}")) for var in var_names
        }
        ArgsModel = create_model(f"{name}_args", **fields)
    else:
        ArgsModel = None

    def execute_tool_with_dict(**kwargs) -> str:
        """Execute shell command with provided arguments."""
        result = execute_shell_tool(config, kwargs)
        if result.success:
            return (
                str(result.output).strip() if result.output is not None else "Success"
            )
        else:
            return f"Error: {result.error}"

    return StructuredTool.from_function(
        func=execute_tool_with_dict,
        name=name,
        description=config.description,
        args_schema=ArgsModel,
    )


def build_python_tool(
    name: str,
    config: PythonToolConfig | SchemaLoaderToolConfig,
    *,
    graph_root: Path | None = None,
) -> Any:
    """Convert Python tool config to LangChain StructuredTool.

    Args:
        name: Tool name for LLM to reference
        config: Python tool configuration

    Returns:
        LangChain StructuredTool
    """
    # Load the Python function
    func = load_python_function(config, graph_root=graph_root, tool_name=name)

    # Build args schema from function signature
    sig = inspect.signature(func)
    fields = {}
    for param_name, param in sig.parameters.items():
        # Skip *args, **kwargs
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        # Get type annotation or default to str
        param_type = (
            param.annotation if param.annotation != inspect.Parameter.empty else str
        )

        # Create field with description
        fields[param_name] = (param_type, Field(description=f"Parameter: {param_name}"))

    # Create dynamic Pydantic model
    ArgsModel = create_model(f"{name}_args", **fields) if fields else None

    def execute_python(**kwargs) -> str:
        """Execute the Python function and return result as string."""
        try:
            result = func(**kwargs)
            return str(result) if result is not None else "Success"
        except Exception as e:
            return f"Error: {e}"

    description = getattr(config, "description", "Load schema data")
    return StructuredTool.from_function(
        func=execute_python,
        name=name,
        description=description,
        args_schema=ArgsModel,
    )
