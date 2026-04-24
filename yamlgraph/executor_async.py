"""Async Prompt Executor - Async interface for LLM calls.

This module provides async versions of execute_prompt for use in
async contexts like web servers or concurrent pipelines.

Note: This is a foundation module. The underlying LLM calls still
use sync HTTP clients wrapped with run_in_executor.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from langchain_core.messages import AIMessageChunk
from pydantic import BaseModel

from yamlgraph.config import DEFAULT_TEMPERATURE
from yamlgraph.executor_base import prepare_messages
from yamlgraph.graph_cache import GRAPH_CACHE as _DEFAULT_CACHE
from yamlgraph.models.streaming import StreamEvent
from yamlgraph.utils.llm_factory import create_llm
from yamlgraph.utils.llm_factory_async import invoke_async

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph
    from langgraph.types import Command

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def prepare_messages_async(
    prompt_name: str,
    variables: dict | None = None,
    provider: str | None = None,
    model: str | None = None,
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
    state: dict | None = None,
) -> tuple[list, str | None, str | None]:
    """Async version of prepare_messages.

    Currently just delegates to the sync version since message preparation
    is not I/O bound. Provided for async context consistency.

    Args:
        prompt_name: Name of the prompt file (without .yaml)
        variables: Variables to substitute in the template
        provider: LLM provider override (None to use YAML/env default)
        model: LLM model override (None to use YAML/env default)
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path
        state: Optional state dict for Jinja2 templates (accessible as {{ state.field }})

    Returns:
        Tuple of (messages list, resolved provider, resolved model)
    """
    return prepare_messages(
        prompt_name,
        variables=variables,
        provider=provider,
        model=model,
        graph_path=graph_path,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
        state=state,
    )


async def execute_prompt_async(
    prompt_name: str,
    variables: dict | None = None,
    output_model: type[T] | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    provider: str | None = None,
    model: str | None = None,
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
    state: dict | None = None,
) -> T | str:
    """Execute a YAML prompt asynchronously.

    Async version of execute_prompt for use in async contexts.

    Args:
        prompt_name: Name of the prompt file (without .yaml)
        variables: Variables to substitute in the template
        output_model: Optional Pydantic model for structured output
        temperature: LLM temperature setting
        provider: LLM provider ("anthropic", "mistral", "openai")
        model: LLM model override (None to use prompt YAML/provider default)
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path
        state: Optional state dict for Jinja2 templates (accessible as {{ state.field }})

    Returns:
        Parsed Pydantic model if output_model provided, else raw string

    Example:
        >>> result = await execute_prompt_async(
        ...     "greet",
        ...     variables={"name": "World"},
        ...     output_model=GenericReport,
        ... )
    """
    messages, resolved_provider, resolved_model = prepare_messages(
        prompt_name=prompt_name,
        variables=variables,
        provider=provider,
        model=model,
        graph_path=graph_path,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
        state=state,
    )

    # Create LLM (cached via factory)
    llm = create_llm(
        temperature=temperature, provider=resolved_provider, model=resolved_model
    )

    # Invoke asynchronously
    return await invoke_async(llm, messages, output_model)


async def execute_prompts_concurrent(
    prompts: list[dict],
) -> list[BaseModel | str]:
    """Execute multiple prompts concurrently.

    Useful for parallel LLM calls in pipelines.

    Args:
        prompts: List of dicts with keys:
            - prompt_name: str (required)
            - variables: dict (optional)
            - output_model: Type[BaseModel] (optional)
            - temperature: float (optional)
            - provider: str (optional)

    Returns:
        List of results in same order as input prompts

    Example:
        >>> results = await execute_prompts_concurrent([
        ...     {"prompt_name": "summarize", "variables": {"text": "..."}},
        ...     {"prompt_name": "analyze", "variables": {"text": "..."}},
        ... ])
    """
    tasks = []
    for prompt_config in prompts:
        task = execute_prompt_async(
            prompt_name=prompt_config["prompt_name"],
            variables=prompt_config.get("variables"),
            output_model=prompt_config.get("output_model"),
            temperature=prompt_config.get("temperature", DEFAULT_TEMPERATURE),
            provider=prompt_config.get("provider"),
        )
        tasks.append(task)

    return await asyncio.gather(*tasks)


# ==============================================================================
# Streaming Support (Phase 3 - Feature 004)
# ==============================================================================


async def execute_prompt_streaming(
    prompt_name: str,
    variables: dict | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    provider: str | None = None,
    model: str | None = None,
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
    state: dict | None = None,
) -> AsyncIterator[str]:
    """Execute a YAML prompt with streaming token output.

    Yields tokens as they are generated by the LLM. Does not support
    structured output (output_model) - use execute_prompt_async for that.

    Args:
        prompt_name: Name of the prompt file (without .yaml)
        variables: Variables to substitute in the template
        temperature: LLM temperature setting
        provider: LLM provider ("anthropic", "mistral", "openai")
        model: LLM model override (None to use prompt YAML/provider default)
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path
        state: Optional state dict for Jinja2 templates (accessible as {{ state.field }})

    Yields:
        Token strings as they are generated

    Example:
        >>> async for token in execute_prompt_streaming("greet", {"name": "World"}):
        ...     print(token, end="", flush=True)
        Hello, World!
    """
    messages, resolved_provider, resolved_model = prepare_messages(
        prompt_name=prompt_name,
        variables=variables,
        provider=provider,
        model=model,
        graph_path=graph_path,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
        state=state,
    )

    # Create LLM (cached via factory)
    llm = create_llm(
        temperature=temperature, provider=resolved_provider, model=resolved_model
    )

    # Stream tokens
    async for chunk in llm.astream(messages):
        content = chunk.content
        if content:  # Skip empty chunks
            yield content


# ==============================================================================
# Async Graph Execution (Phase 2 - Feature 003)
# ==============================================================================


async def run_graph_async(
    app,
    initial_state: dict,
    config: dict | None = None,
) -> dict:
    """Execute a compiled graph asynchronously.

    Thin wrapper around LangGraph's ainvoke for consistent API.
    Supports interrupt handling and Command resume.

    Args:
        app: Compiled LangGraph app (from graph.compile())
        initial_state: Initial state dict or Command(resume=...) for resuming
        config: LangGraph config with thread_id, e.g.
                {"configurable": {"thread_id": "my-thread"}}

    Returns:
        Final state dict. If interrupted, contains "__interrupt__" key.

    Example:
        >>> app = load_and_compile_async("graphs/interview.yaml")
        >>> result = await run_graph_async(
        ...     app,
        ...     {"query": "hello"},
        ...     {"configurable": {"thread_id": "t1"}},
        ... )
        >>> if "__interrupt__" in result:
        ...     # Handle interrupt - get user input
        ...     result = await run_graph_async(
        ...         app,
        ...         Command(resume="user answer"),
        ...         {"configurable": {"thread_id": "t1"}},
        ...     )
    """
    config = config or {}
    return await app.ainvoke(initial_state, config)


async def compile_graph_async(
    graph,
    config,
) -> CompiledStateGraph:
    """Compile a StateGraph with async-compatible checkpointer.

    Uses get_checkpointer_async() to properly initialize async Redis savers.

    Args:
        graph: StateGraph instance
        config: GraphConfig with optional checkpointer field

    Returns:
        Compiled graph ready for ainvoke()
    """
    from yamlgraph.storage.checkpointer_factory import get_checkpointer_async

    checkpointer_config = getattr(config, "checkpointer", None)
    checkpointer = await get_checkpointer_async(checkpointer_config)

    return graph.compile(checkpointer=checkpointer)


async def load_and_compile_async(
    path: str,
    *,
    cache: dict[str, Any] | None = _DEFAULT_CACHE,
) -> CompiledStateGraph:
    """Load YAML and compile to async-ready graph.

    Uses the process-global GRAPH_CACHE by default so compiled graphs survive
    module reloads and are shared across all callers within the same process.

    Args:
        path: Path to YAML graph definition
        cache: Dict to cache compiled graphs in. Defaults to the process-global
            GRAPH_CACHE. Pass ``None`` to disable caching (for test isolation).

    Returns:
        Compiled graph ready for ainvoke()

    Example:
        >>> app = await load_and_compile_async("graphs/interview.yaml")
        >>> result = await run_graph_async(app, {"input": "hi"}, config)
    """
    if cache is not None and path in cache:
        logger.debug("Cache hit: %s", path)
        return cache[path]

    from yamlgraph.graph_loader import compile_graph, load_graph_config

    logger.info("Compiling graph: %s", path)
    config = load_graph_config(path)
    logger.info("Loaded graph config: %s v%s", config.name, config.version)

    state_graph = compile_graph(config)
    compiled = await compile_graph_async(state_graph, config)

    if cache is not None:
        cache[path] = compiled

    return compiled


# ==============================================================================
# ==============================================================================
# Native LangGraph Streaming (FR-029 - REQ-YG-048, REQ-YG-049, REQ-YG-065)
# FR-062: Error propagation, timeout, and interrupt detection (REQ-YG-077)
# ==============================================================================


def _get_interrupt_payload(state) -> object:  # noqa: ANN001 — StateSnapshot type
    """Extract interrupt payload from state snapshot.

    Args:
        state: LangGraph StateSnapshot from aget_state()

    Returns:
        Interrupt payload value, or None if no interrupts pending.
    """
    if state.tasks and state.tasks[-1].interrupts:
        return state.tasks[-1].interrupts[-1].value
    return None


async def run_graph_streaming_native(
    graph_path: str,
    initial_state: dict | Command,
    config: dict | None = None,
    node_filter: str | None = None,
    subgraphs: bool = False,
    yield_events: bool = True,
    timeout: float | None = None,
) -> AsyncIterator[str | StreamEvent]:
    """Execute graph with native LangGraph token streaming.

    Uses LangGraph's astream(stream_mode="messages") for true token-by-token
    streaming from ALL LLM nodes in the graph. Supports multi-turn resume
    via Command(resume=...) and config with thread_id.

    FR-062: Wraps the streaming generator with error propagation and timeout
    support. On exception, yields StreamEvent(type="error") instead of crashing
    silently. On graph interrupt (with thread_id), yields StreamEvent(type="interrupt").

    Args:
        graph_path: Path to graph YAML file
        initial_state: Initial state dict, or Command(resume=...) for resuming
        config: LangGraph config, e.g. {"configurable": {"thread_id": "t1"}}
        node_filter: If set, only yield tokens from this node name
        subgraphs: If True, also stream tokens from subgraph nodes (mode=direct).
        yield_events: If True (default), yield StreamEvent on error/interrupt.
            If False, raise exceptions to caller (pre-FR-062 behavior).
        timeout: Total stream timeout in seconds. None means no timeout.

    Yields:
        str: Token strings from LLM nodes
        StreamEvent: Error or interrupt control signals (when yield_events=True)
    """
    app = await load_and_compile_async(graph_path)
    config = config or {}

    try:
        async with asyncio.timeout(timeout):
            async for event in app.astream(
                initial_state, config, stream_mode="messages", subgraphs=subgraphs
            ):
                # Event structure depends on subgraphs flag:
                # - subgraphs=False: (AIMessageChunk, metadata_dict)
                # - subgraphs=True: (namespace_tuple, (AIMessageChunk, metadata_dict))
                if subgraphs:
                    _namespace, payload = event
                    chunk, metadata = payload
                else:
                    chunk, metadata = event

                # Filter by node name if specified
                node_name = metadata.get("langgraph_node")
                if node_filter and node_name != node_filter:
                    continue

                # Yield token content — only AI message chunks without tool calls.
                # Agent nodes emit System, Human, Tool, and intermediate AI messages;
                # only the final AI answer should reach clients (FR-058).
                # Router nodes emit dict content which is also filtered out.
                if (
                    isinstance(chunk, AIMessageChunk)
                    and chunk.content
                    and isinstance(chunk.content, str)
                    and not chunk.tool_calls
                ):
                    yield chunk.content
    except TimeoutError:
        logger.warning("Streaming timeout after %s seconds for %s", timeout, graph_path)
        if yield_events:
            yield StreamEvent(
                type="error",
                error=f"Stream timed out after {timeout}s",
                error_type="TimeoutError",
            )
        else:
            raise
    except Exception as exc:
        logger.error("Streaming error in %s: %s", graph_path, exc)
        if yield_events:
            yield StreamEvent(
                type="error",
                error=str(exc),
                error_type=type(exc).__name__,
            )
        else:
            raise
    finally:
        # Interrupt detection — only when a thread_id is configured
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id:
            try:
                state = await app.aget_state(config)
                interrupt_payload = _get_interrupt_payload(state)
                if interrupt_payload is not None:
                    yield StreamEvent(
                        type="interrupt",
                        payload=interrupt_payload,
                    )
            except Exception:
                logger.debug("Could not check interrupt state", exc_info=True)


__all__ = [
    "execute_prompt_async",
    "execute_prompt_streaming",
    "execute_prompts_concurrent",
    "prepare_messages_async",
    "run_graph_async",
    "run_graph_streaming_native",
    "compile_graph_async",
    "load_and_compile_async",
]
