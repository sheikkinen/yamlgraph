"""Per-node timeout wrapping (FR-069).

Extracted from node_compiler.py (FR-677) to keep that module under the
450-line ceiling. Behavior-preserving.
"""

from __future__ import annotations

import concurrent.futures
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def _maybe_wrap_timeout(
    node_fn: Callable,
    node_config: dict[str, Any],
    node_name: str,
) -> Callable:
    """Wrap node function with ThreadPoolExecutor timeout if configured.

    FR-069: Per-node timeout bounding. When timeout is set, the node
    function is executed in a one-shot ThreadPoolExecutor. On
    concurrent.futures.TimeoutError, a PipelineError with
    error_type=TIMEOUT_ERROR is returned.

    Args:
        node_fn: The original node function
        node_config: Node configuration dict (checked for 'timeout')
        node_name: Name of the node (for error messages)

    Returns:
        Wrapped function if timeout is set, original function otherwise
    """
    timeout = node_config.get("timeout")
    if timeout is None:
        return node_fn

    state_key = node_config.get("state_key", node_name)

    def timed_fn(state: dict) -> dict:
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            return pool.submit(node_fn, state).result(timeout=timeout)
        except concurrent.futures.TimeoutError as e:
            from yamlgraph.models import PipelineError
            from yamlgraph.models.schemas import ErrorType

            pe = PipelineError.from_exception(
                e, node=node_name, error_type=ErrorType.TIMEOUT_ERROR
            )
            return {
                state_key: None,
                "current_step": node_name,
                "errors": [pe],
            }
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    timed_fn.__name__ = getattr(node_fn, "__name__", f"{node_name}_node")
    return timed_fn


__all__ = ["_maybe_wrap_timeout"]
