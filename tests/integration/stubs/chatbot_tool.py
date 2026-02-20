"""Stub chatbot tool for FR-049 interactive_tool integration tests.

Simulates a stateful multi-turn chatbot session.
No WebSocket, no LLM — pure deterministic state manipulation.
Inspired by projects/ninchat/tools/inquiry.py.
"""

from __future__ import annotations

# In-memory session store (reset between tests)
_sessions: dict[str, dict] = {}


def chatbot_start(state: dict) -> dict:
    """Start a new chatbot session. Returns greeting."""
    session_id = f"session-{len(_sessions) + 1}"
    _sessions[session_id] = {"turn": 0, "history": []}
    return {
        "session_id": session_id,
        "bot_response": "Hello! I'm a stub chatbot. How can I help?",
        "session_done": False,
    }


def chatbot_step(state: dict) -> dict:
    """Process user message. Returns bot response."""
    session_id = state.get("session_id", "")
    user_message = state.get("user_message", "")
    session = _sessions.get(session_id, {"turn": 0, "history": []})

    session["turn"] += 1
    session["history"].append(user_message)

    # Deterministic responses
    if "bye" in user_message.lower() or "quit" in user_message.lower():
        return {
            "bot_response": "Goodbye! Session complete.",
            "session_done": True,
        }

    if session["turn"] >= 5:
        return {
            "bot_response": f"Max turns reached (turn {session['turn']}). Ending.",
            "session_done": True,
        }

    return {
        "bot_response": f"Turn {session['turn']}: You said '{user_message}'",
        "session_done": False,
    }


def chatbot_end(state: dict) -> dict:
    """Close session. Returns summary."""
    session_id = state.get("session_id", "")
    session = _sessions.pop(session_id, {"turn": 0, "history": []})
    return {
        "session_summary": f"Session {session_id}: {session['turn']} turns",
    }


def reset_sessions() -> None:
    """Test helper: clear all sessions."""
    _sessions.clear()
