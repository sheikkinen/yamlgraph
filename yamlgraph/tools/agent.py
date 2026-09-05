"""Agent node factory for LLM-driven tool loops.

This module provides the agent node type that allows the LLM to
autonomously decide which tools to call until it has enough
information to provide a final answer.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from pydantic import ValidationError

from yamlgraph.executor_base import format_prompt
from yamlgraph.tools.python_tool import PythonToolConfig
from yamlgraph.tools.schema_loader_tool import SchemaLoaderToolConfig
from yamlgraph.tools.shell import ShellToolConfig
from yamlgraph.tools.tool_builders import build_langchain_tool, build_python_tool
from yamlgraph.utils.content import normalize_content as _normalize_content
from yamlgraph.utils.guard_runtime import (
    enforce_post_guards,
    enforce_pre_guards,
    extract_guard_rules,
)
from yamlgraph.utils.json_extract import extract_json
from yamlgraph.utils.llm_factory import create_llm
from yamlgraph.utils.prompts import load_prompt
from yamlgraph.utils.structured_output import (
    bind_structured_output,
    invoke_structured,
)

logger = logging.getLogger(__name__)


class AllToolCallsFailedError(Exception):
    """Every tool call in an agent run failed (FR-891, fail-closed).

    Mirrors race_node.AllCandidatesFailedError: raised before final
    synthesis so error strings are never laundered into fluent output.
    """


def _check_all_tools_failed(node_name: str, tool_results: list[dict]) -> None:
    """Raise when tool_results is non-empty and every call failed (FR-891)."""
    if not tool_results or any(r["success"] for r in tool_results):
        return
    tool_names = sorted({r["tool"] for r in tool_results})
    first_failure = tool_results[0]["output"]
    raise AllToolCallsFailedError(
        f"Agent node '{node_name}': all {len(tool_results)} tool call(s) "
        f"failed ({len(tool_results)} failure(s); tools: {', '.join(tool_names)}; "
        f"first failure: {first_failure})"
    )


def _try_structured_output(
    content: str | list,
    msgs: list,
    output_model: type | None,
    llm_base: Any,
) -> Any:
    """Try to extract structured output, fallback to LLM re-invoke (FR-448).

    Falls back to lenient construction when provider rejects response_format (FR-456).
    """
    if not output_model:
        return _normalize_content(content)
    # Normalize content — Anthropic returns list of content blocks
    text = _normalize_content(content)
    # Try parse first (cheap). FR-678: catch only ValidationError — a schema
    # mismatch in extracted JSON is a legitimate fallback trigger. Programming
    # defects (TypeError, AttributeError) and a broken extract_json (ValueError)
    # must propagate instead of being masked as an expensive LLM re-invoke.
    parsed = extract_json(text)
    if isinstance(parsed, dict):
        try:
            return output_model.model_validate(parsed).model_dump()
        except ValidationError as parse_exc:
            logger.warning(
                "Structured output parse failed (%s), retrying with LLM",
                type(parse_exc).__name__,
            )
    # Structured re-invoke: ask LLM again with schema enforcement (expensive)
    # Append a user message so the conversation ends with a user turn —
    # Anthropic rejects assistant prefill when msgs ends with assistant.
    from langchain_core.messages import HumanMessage

    retry_msgs = list(msgs) + [
        HumanMessage(content="Now produce your response as structured JSON output.")
    ]
    try:
        # FR-998: the policy owns invocation too — one typed second attempt
        # for an Anthropic model that rejects constrained decoding.
        return invoke_structured(llm_base, output_model, retry_msgs).model_dump()
    except Exception as reinvoke_err:
        err_str = str(reinvoke_err)
        # FR-458: OpenAI strict mode rejects schemas without additionalProperties
        # FR-809: DeepSeek rejects response_format outright ("This
        # response_format type is unavailable now") — same cure
        if (
            "invalid_json_schema" in err_str
            or "additionalProperties" in err_str
            or "response_format" in err_str
        ):
            logger.warning("Strict schema rejected, retrying with function_calling")
            fc_llm = bind_structured_output(
                llm_base, output_model, method="function_calling"
            )
            try:
                return fc_llm.invoke(retry_msgs).model_dump()
            except Exception as fc_err:
                # FR-456: If extract_json found a dict, use lenient construction
                if isinstance(parsed, dict):
                    logger.warning(
                        "Structured output API rejected, returning best-effort "
                        "parse: %s",
                        fc_err,
                    )
                    return output_model.model_construct(**parsed).model_dump()
                # FR-809: DeepSeek thinking mode rejects tool_choice too —
                # last tier is a plain re-invoke, parsing JSON from raw text.
                # Unparseable output raises; nothing is fabricated.
                logger.warning(
                    "Structured retry rejected (%s), plain re-invoke", fc_err
                )
                plain = _normalize_content(llm_base.invoke(retry_msgs).content)
                plain_parsed = extract_json(plain)
                if isinstance(plain_parsed, dict):
                    return output_model.model_validate(plain_parsed).model_dump()
                raise
        # FR-456: If extract_json found a dict, use lenient construction
        if isinstance(parsed, dict):
            logger.warning(
                "Structured output API rejected, returning best-effort parse: %s",
                reinvoke_err,
            )
            return output_model.model_construct(**parsed).model_dump()
        raise


def create_agent_node(  # noqa: C901
    node_name: str,
    node_config: dict[str, Any],
    tools: dict[str, ShellToolConfig],
    python_tools: dict[str, PythonToolConfig | SchemaLoaderToolConfig] | None = None,
    *,
    defaults: dict[str, Any] | None = None,
    graph_path: Path | None = None,
    output_model: type | None = None,
    graph_tool_configs: dict[str, Any] | None = None,
    graph_tool_callables: dict[str, Callable] | None = None,
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
    if graph_tool_configs is None:
        graph_tool_configs = {}
    if graph_tool_callables is None:
        graph_tool_callables = {}

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
    guards_pre, guards_post = extract_guard_rules(node_config)

    # Build LangChain tools from configs
    lc_tools = []
    tool_lookup = {}

    graph_root = graph_path.parent.resolve() if graph_path else None
    for name in tool_names:
        if name in tools:
            st = build_langchain_tool(name, tools[name])
            lc_tools.append(st)
            tool_lookup[name] = st
        elif name in python_tools:
            st = build_python_tool(name, python_tools[name], graph_root=graph_root)
            lc_tools.append(st)
            tool_lookup[name] = st
        elif name in graph_tool_configs and name in graph_tool_callables:
            from yamlgraph.tools.graph_tool import build_graph_tool

            st = build_graph_tool(
                name, graph_tool_configs[name], graph_tool_callables[name]
            )
            lc_tools.append(st)
            tool_lookup[name] = st
        else:
            logger.warning(
                f"Tool '{name}' not found in shell, python, or graph registries"
            )

    def node_fn(state: dict) -> dict:
        """Execute the agent loop."""
        # FR-677: pre-guards run before the agent loop.
        if enforce_pre_guards(node_name, guards_pre, state):
            from yamlgraph.error_handlers import build_skip_error_state

            return build_skip_error_state(
                node_name=node_name,
                state_key=state_key,
                error_message=f"Agent node '{node_name}' skipped by pre-guard",
                state=state,
            )

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
        # FR-451: Use `is not None` for temperature — 0 is falsy but valid
        resolved_temperature = next(
            (
                v
                for src in (node_config, defaults, prompt_config)
                if (v := src.get("temperature")) is not None
            ),
            0.7,
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
                # FR-891: fail closed before synthesis — the witnessed
                # incident finalized on this path with 6/6 failed calls.
                _check_all_tools_failed(node_name, tool_results)
                # Return only NEW messages (delta) — the add reducer
                # appends to existing state, so returning the full list
                # would cause quadratic growth (FR-057).
                new_messages = messages[len(existing_messages) :]
                final_value = _try_structured_output(
                    response.content, messages, output_model, llm_base
                )
                # FR-677: post-guards validate the agent's final answer.
                final_value = enforce_post_guards(
                    node_name, guards_post, state, final_value
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

                # Execute the tool via unified StructuredTool.invoke (FR-660)
                tool_obj = tool_lookup.get(tool_name)
                if tool_obj:
                    try:
                        output = str(tool_obj.invoke(tool_args))
                        success = not output.startswith("Error: ")
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
        # FR-891: fail closed on the max-iterations path too (judgement R-1).
        _check_all_tools_failed(node_name, tool_results)
        last_content = messages[-1].content if hasattr(messages[-1], "content") else ""
        final_value = _try_structured_output(
            last_content, messages, output_model, llm_base
        )
        # FR-677: post-guards validate the agent's final answer.
        final_value = enforce_post_guards(node_name, guards_post, state, final_value)
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
