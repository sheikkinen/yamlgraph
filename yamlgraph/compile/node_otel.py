"""Per-node OpenTelemetry span wrapping (FR-759).

Mirrors ``node_timeout.py``'s wrapping pattern: every compiled node
function is wrapped unconditionally at compile time, but the wrapper
itself checks :func:`yamlgraph.observability.otel.is_otel_enabled` at
call time, so a disabled run pays only a single environment lookup —
no OpenTelemetry import, no span, no behavior change (AC-03).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


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

    def otel_wrapped(state: dict) -> Any:
        from yamlgraph.observability import otel

        if not otel.is_otel_enabled():
            return node_fn(state)

        with otel.node_execution_span(node_name, node_type) as node_ctx:
            result = node_fn(state)
            if isinstance(result, dict):
                node_ctx.keys_written = list(result.keys())
            return result

    otel_wrapped.__name__ = getattr(node_fn, "__name__", f"{node_name}_node")
    return otel_wrapped


__all__ = ["_maybe_wrap_otel"]
