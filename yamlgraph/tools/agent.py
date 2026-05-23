"""Agent node factory for LLM-driven tool loops.

This module provides the agent node type that allows the LLM to
autonomously decide which tools to call until it has enough
information to provide a final answer.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from yamlgraph.executor_base import format_prompt
from yamlgraph.tools.python_tool import PythonToolConfig, load_python_function
from yamlgraph.tools.schema_loader_tool import SchemaLoaderToolConfig
from yamlgraph.tools.shell import ShellToolConfig, execute_shell_tool
from yamlgraph.utils.content import normalize_content as _normalize_content
from yamlgraph.utils.json_extract import extract_json
from yamlgraph.utils.llm_factory import create_llm
from yamlgraph.utils.prompts import load_prompt

logger = logging.getLogger(__name__)


def build_langchain_tool(name: str, config: ShellToolConfig) -> Callable:
    """Convert shell config to LangChain Tool.

    Args:
        name: Tool name for LLM to reference
        config: Shell tool configuration

    Returns:
        LangChain-compatible tool function
    """
    import re

    from langchain_core.tools import StructuredTool
    from pydantic import Field, create_model

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
    from langchain_core.tools import StructuredTool
    from pydantic import Field, create_model

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


def _try_structured_output(
    content: str,
    msgs: list,
    output_model: type | None,
    llm_base: Any,
) -> Any:
    """Try to extract structured output, fallback to LLM re-invoke (FR-448)."""
    if not output_model:
        return _normalize_content(content)
    # Try parse first (cheap)
    try:
        parsed = extract_json(content)
        if isinstance(parsed, dict):
            return output_model.model_validate(parsed).model_dump()
    except Exception:
        logger.debug("JSON parse failed for structured output, falling back to LLM")
    # Fallback: structured output re-invoke (expensive)
    structured_llm = llm_base.with_structured_output(output_model)
    result = structured_llm.invoke(msgs)
    return result.model_dump()


def create_agent_node(  # noqa: C901
    node_name: str,
    node_config: dict[str, Any],
    tools: dict[str, ShellToolConfig],
    python_tools: dict[str, PythonToolConfig | SchemaLoaderToolConfig] | None = None,
    *,
    defaults: dict[str, Any] | None = None,
    graph_path: Path | None = None,
    output_model: type | None = None,
) -> Callable[[dict], dict]:
    """Create an agent node that loops with tool calls.

    The agent will:
    1. Send the prompt to the LLM with available tools
    2. If LLM returns tool calls, execute them and feed results back
    3. Repeat until LLM returns without tool calls or max_iterations reached

    Args:
        node_name: Name of the node in the graph
        node_config: Node configuration from YAML
        tools: Registry of available shell tools
        python_tools: Registry of Python tools (PythonToolConfig)
        defaults: Default configuration including prompts_relative/prompts_dir
        graph_path: Path to graph YAML file (for relative prompt resolution)

    Returns:
        Node function that runs the agent loop

    Config options:
        - tools: List of tool names to make available
        - max_iterations: Max tool-call loops (default: 10)
        - state_key: Key to store final answer (default: node_name)
        - prompt: Prompt file name (default: "agent")
        - tool_results_key: Optional key to store raw tool outputs
    """
    if defaults is None:
        defaults = {}
    if python_tools is None:
        python_tools = {}

    # Extract prompts config from defaults (consistent with llm_nodes.py)
    prompts_relative = defaults.get("prompts_relative", False)
    prompts_dir = defaults.get("prompts_dir")
    if prompts_dir:
        prompts_dir = Path(prompts_dir)

    tool_names = node_config.get("tools", [])
    max_iterations = node_config.get("max_iterations", 10)
    state_key = node_config.get("state_key", node_name)
    prompt_name = node_config.get("prompt", "agent")
    tool_results_key = node_config.get("tool_results_key")

    # Build LangChain tools from configs
    lc_tools = []
    tool_lookup = {}

    graph_root = graph_path.parent.resolve() if graph_path else None
    for name in tool_names:
        if name in tools:
            # Shell tool - need to wrap
            lc_tools.append(build_langchain_tool(name, tools[name]))
            tool_lookup[name] = tools[name]
        elif name in python_tools:
            # Python tool - wrap as LangChain tool
            lc_tools.append(
                build_python_tool(name, python_tools[name], graph_root=graph_root)
            )
            tool_lookup[name] = python_tools[name]
        else:
            logger.warning(f"Tool '{name}' not found in shell or python registries")

    def node_fn(state: dict) -> dict:
        """Execute the agent loop."""
        # Load prompts - fail fast if missing
        prompt_config = load_prompt(
            prompt_name,
            prompts_dir=prompts_dir,
            graph_path=graph_path,
            prompts_relative=prompts_relative,
        )
        user_template = prompt_config.get("user", "{input}")

        # Resolve LLM config: node_config > defaults > prompt_config > None
        resolved_provider = (
            node_config.get("provider")
            or defaults.get("provider")
            or prompt_config.get("provider")
        )
        resolved_model = (
            node_config.get("model")
            or defaults.get("model")
            or prompt_config.get("model")
        )
        resolved_temperature = (
            node_config.get("temperature")
            or defaults.get("temperature")
            or prompt_config.get("temperature")
            or 0.7  # Default temperature for agents
        )

        # Format prompts using format_prompt (supports Jinja2 and simple vars)
        # Pass state as both 'state' parameter and merged into variables for flexibility
        system_prompt = format_prompt(
            prompt_config.get("system", ""),
            variables=state,
            state=state,
        )
        user_prompt = format_prompt(
            user_template,
            variables=state,
            state=state,
        )

        # Initialize messages - preserve existing if multi-turn
        existing_messages = list(state.get("messages", []))
        if existing_messages:
            # Multi-turn: add new user message to existing conversation
            messages = existing_messages + [HumanMessage(content=user_prompt)]
        else:
            # New conversation: start with system + user
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

        # Track raw tool outputs for persistence
        tool_results: list[dict] = []

        # Resolve output model for structured output (FR-448)
        # output_model is passed from the caller (node_compiler.py)

        # Save base LLM before binding tools — with_structured_output
        # and bind_tools are mutually exclusive on most providers (FR-448)
        llm_base = create_llm(
            provider=resolved_provider,
            model=resolved_model,
            temperature=resolved_temperature,
        )
        llm = llm_base.bind_tools(lc_tools)

        logger.info(
            f"🤖 Starting agent loop: {node_name} (max {max_iterations} iterations)"
        )
        logger.debug(f"Tools available: {[t.name for t in lc_tools]}")
        logger.debug(f"User prompt: {user_prompt[:100]}...")

        for iteration in range(max_iterations):
            logger.debug(f"Agent iteration {iteration + 1}/{max_iterations}")

            # Get LLM response
            response = llm.invoke(messages)
            messages.append(response)

            logger.debug(f"Response tool_calls: {response.tool_calls}")

            # Check if LLM wants to call tools
            if not response.tool_calls:
                # Done - LLM finished reasoning
                logger.info(f"✓ Agent completed after {iteration + 1} iterations")
                # Return only NEW messages (delta) — the add reducer
                # appends to existing state, so returning the full list
                # would cause quadratic growth (FR-057).
                new_messages = messages[len(existing_messages) :]
                final_value = _try_structured_output(
                    response.content, messages, output_model, llm_base
                )
                result = {
                    state_key: final_value,
                    "current_step": node_name,
                    "_agent_iterations": iteration + 1,
                    "messages": new_messages,
                }
                if tool_results_key and tool_results:
                    result[tool_results_key] = tool_results
                return result

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call.get("id", f"call_{iteration}")

                logger.info(f"🔧 Calling tool: {tool_name}({tool_args})")

                # Execute the tool
                tool_config = tool_lookup.get(tool_name)
                if tool_config:
                    # Check the type of tool config
                    if isinstance(tool_config, ShellToolConfig):
                        # Shell tool - use execute_shell_tool
                        result = execute_shell_tool(tool_config, tool_args)
                        output = (
                            str(result.output)
                            if result.success
                            else f"Error: {result.error}"
                        )
                        success = result.success
                    elif isinstance(
                        tool_config, PythonToolConfig | SchemaLoaderToolConfig
                    ):
                        # Python tool - load and execute function
                        try:
                            func = load_python_function(
                                tool_config,
                                graph_root=graph_root,
                                tool_name=tool_name,
                            )
                            output = str(func(**tool_args))
                            success = True
                        except Exception as e:
                            output = f"Error: {e}"
                            success = False
                    else:
                        # LangChain tool (websearch, etc) - invoke directly
                        try:
                            output = tool_config.invoke(tool_args)
                            success = True
                        except Exception as e:
                            output = f"Error: {e}"
                            success = False
                else:
                    output = f"Error: Unknown tool '{tool_name}'"
                    success = False

                # Store raw tool result for persistence
                tool_results.append(
                    {
                        "tool": tool_name,
                        "args": tool_args,
                        "output": output,
                        "success": success,
                    }
                )

                # Add tool result to messages
                messages.append(ToolMessage(content=output, tool_call_id=tool_id))

        # Hit max iterations
        logger.warning(f"Agent hit max iterations ({max_iterations})")
        last_content = messages[-1].content if hasattr(messages[-1], "content") else ""
        final_value = _try_structured_output(
            last_content, messages, output_model, llm_base
        )
        # Return only NEW messages (delta) — see FR-057
        new_messages = messages[len(existing_messages) :]
        result = {
            state_key: final_value,
            "current_step": node_name,
            "_agent_iterations": max_iterations,
            "_agent_limit_reached": True,
            "messages": new_messages,
        }
        if tool_results_key and tool_results:
            result[tool_results_key] = tool_results
        return result

    return node_fn
