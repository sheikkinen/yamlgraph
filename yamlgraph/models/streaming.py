"""Streaming control signals for run_graph_streaming_native().

FR-062: StreamEvent provides typed error/interrupt signals during streaming,
replacing silent generator death with explicit control events.
"""

from typing import Any, Literal

from pydantic import BaseModel


class StreamEvent(BaseModel):
    """Control signal yielded during streaming (Commandment 5: Pydantic for all typed data).

    Yielded alongside str tokens by run_graph_streaming_native() when
    yield_events=True (default). Consumers must check isinstance(item, StreamEvent)
    to handle errors and interrupts.

    Attributes:
        type: "error" for exceptions/timeouts, "interrupt" for graph pauses.
        error: Human-readable error message (error events only).
        error_type: Exception class name, e.g. "TimeoutError" (error events only).
        payload: Interrupt payload from graph state (interrupt events only).
    """

    type: Literal["error", "interrupt"]
    error: str | None = None
    error_type: str | None = None
    payload: Any = None
