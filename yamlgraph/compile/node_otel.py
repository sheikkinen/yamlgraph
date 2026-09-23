"""Per-node OpenTelemetry span wrapping (FR-759).

Mirrors ``node_timeout.py``'s wrapping pattern: every compiled node
function is wrapped unconditionally at compile time, but the wrapper
itself checks :func:`yamlgraph.observability.otel.is_otel_enabled` at
call time, so a disabled run pays only a single environment lookup —
no OpenTelemetry import, no span, no behavior change (AC-03).
"""

# No `from __future__ import annotations` here: it stringifies the wrapper's
# `config` annotation, and LangGraph decides whether to inject RunnableConfig
# by inspecting that annotation as a real type (FR-1058).

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.config import call_func_with_variable_args


def _maybe_wrap_otel(
    node_fn: Callable,
    node_name: str,
    node_type: str,
) -> Callable:
    """Wrap ``node_fn`` to emit a ``yamlgraph.node.execute`` span when enabled.

    Args:
        node_fn: The original node function.
        node_name: Node id from the graph YAML (span attribute).
        node_type: Node factory type, e.g. "llm", "tool" (span attribute).

    Returns:
        A wrapped callable with identical behavior when OTEL is disabled.
    """

    # Declares (state, config) so LangGraph's arity inspection still injects
    # RunnableConfig; the dispatch below forwards it only to nodes that
    # accept it, keeping the disabled path a true no-op (FR-1058).
    def otel_wrapped(state: dict, config: RunnableConfig | None = None) -> Any:
        from yamlgraph.observability import otel

        if not otel.is_otel_enabled():
            return call_func_with_variable_args(node_fn, state, config or {})

        with otel.node_execution_span(node_name, node_type) as node_ctx:
            result = call_func_with_variable_args(node_fn, state, config or {})
            if isinstance(result, dict):
                node_ctx.keys_written = list(result.keys())
            return result

    otel_wrapped.__name__ = getattr(node_fn, "__name__", f"{node_name}_node")
    return otel_wrapped


def node_config_get(node_config: object, key: str, default: object) -> object:
    """Read a key from node_config, whether it's a dict or an attr-object.

    Shared by compile handlers that need to inspect the declared YAML
    config for a node without assuming its concrete representation
    (FR-759 P3: llm/router share one handler and must report the
    node's actual declared type, not a hardcoded one).
    """
    if isinstance(node_config, dict):
        return node_config.get(key, default)
    return getattr(node_config, key, default)


__all__ = ["_maybe_wrap_otel", "node_config_get"]
