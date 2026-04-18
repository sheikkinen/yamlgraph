"""Execution timing callback (FR-231 Phase 1, REQ-YG-231).

Provides a LangChain callback handler that tracks wall-clock duration
of each LLM call in a graph run.  Follows the same injection pattern
as :class:`yamlgraph.utils.token_tracker.TokenUsageCallbackHandler`.

Usage::

    from yamlgraph.utils.timing_tracker import create_timing_tracker

    timer = create_timing_tracker()
    config.setdefault("callbacks", []).append(timer)
    result = app.invoke(state, config=config)

    if timer.total_calls > 0:
        print(timer.summary())
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class ExecutionTimingCallbackHandler(BaseCallbackHandler):
    """Tracks wall-clock duration of each LLM call in a graph run.

    Works transparently with ``graph.invoke()`` via LangGraph's
    ``contextvars``-based callback propagation — no modification to
    node functions required.
    """

    def __init__(self) -> None:
        super().__init__()
        self.total_duration: float = 0.0
        self.total_calls: int = 0
        self.call_durations: list[float] = []
        self._start_time: float | None = None

    # -- LangChain callbacks ---------------------------------------------------

    def on_llm_start(
        self,
        _serialized: dict[str, Any],  # noqa: ARG002
        _prompts: list[str],  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Record start time before LLM call."""
        self._start_time = time.monotonic()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:  # noqa: ARG002
        """Record elapsed time after LLM call completes."""
        if self._start_time is not None:
            elapsed = time.monotonic() - self._start_time
            self.total_duration += elapsed
            self.call_durations.append(elapsed)
            self.total_calls += 1
            self._start_time = None

    # -- Public API ------------------------------------------------------------

    def summary(self) -> dict[str, float | int]:
        """Return accumulated timing data as a plain dict.

        Returns:
            Dict with ``total_duration_s``, ``call_count``, ``mean_duration_s``.
        """
        return {
            "total_duration_s": round(self.total_duration, 2),
            "call_count": self.total_calls,
            "mean_duration_s": round(self.total_duration / max(self.total_calls, 1), 2),
        }


def create_timing_tracker() -> ExecutionTimingCallbackHandler:
    """Factory — mirrors :func:`yamlgraph.utils.token_tracker.create_token_tracker`.

    Returns:
        A fresh :class:`ExecutionTimingCallbackHandler` instance.
    """
    return ExecutionTimingCallbackHandler()
