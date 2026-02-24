"""MCP session context for sampling backend (REQ-YG-088).

Provides ContextVar-based threading of MCP session from tool handler
to copilot node execution path. This avoids polluting graph state with
infrastructure concerns.

FR-082: MCP Sampling Backend for Copilot Node
"""

import asyncio
import contextvars
from typing import Any

_mcp_session: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "_mcp_session", default=None
)
_mcp_loop: contextvars.ContextVar[asyncio.AbstractEventLoop | None] = (
    contextvars.ContextVar("_mcp_loop", default=None)
)


def set_mcp_context(session: Any, loop: asyncio.AbstractEventLoop | None) -> None:
    """Set the MCP session and event loop for the current context.

    Args:
        session: MCP session object (from server.request_context.session)
        loop: Event loop to use for async operations
    """
    _mcp_session.set(session)
    _mcp_loop.set(loop)


def get_mcp_context() -> tuple[Any, asyncio.AbstractEventLoop | None]:
    """Get the MCP session and event loop from the current context.

    Returns:
        Tuple of (session, loop). Both may be None if not in MCP context.
    """
    return _mcp_session.get(), _mcp_loop.get()


__all__ = ["set_mcp_context", "get_mcp_context"]
