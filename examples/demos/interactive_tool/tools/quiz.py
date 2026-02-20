"""Trivia quiz tools for interactive_tool demo.

A simple multi-turn quiz where the bot asks trivia questions
and the user answers. Demonstrates the interactive_tool pattern:
  - start: initialise session with greeting
  - step: evaluate answer, ask next question (or end)
  - end: summarise score

No LLM needed — pure deterministic logic.
"""

from __future__ import annotations

# Hard-coded trivia bank (keeps demo self-contained)
_QUESTIONS = [
    {"q": "What is the capital of Finland?", "a": "helsinki"},
    {"q": "How many sides does a hexagon have?", "a": "6"},
    {"q": "What planet is closest to the Sun?", "a": "mercury"},
]

_sessions: dict[str, dict] = {}


def quiz_start(state: dict) -> dict:
    """Initialise a new quiz session."""
    sid = f"quiz-{len(_sessions) + 1}"
    _sessions[sid] = {"score": 0, "index": 0, "total": len(_QUESTIONS)}
    first = _QUESTIONS[0]["q"]
    return {
        "session_id": sid,
        "bot_response": (
            f"🎯 Welcome to the trivia quiz! ({len(_QUESTIONS)} questions)\n\n"
            f"Q1: {first}"
        ),
        "session_done": False,
    }


def quiz_step(state: dict) -> dict:
    """Evaluate the user's answer and serve the next question."""
    sid = state.get("session_id", "")
    answer = (state.get("user_answer") or "").strip()
    session = _sessions.get(sid, {"score": 0, "index": 0, "total": len(_QUESTIONS)})

    idx = session["index"]
    correct_answer = _QUESTIONS[idx]["a"]

    # Score the answer
    if answer.lower() == correct_answer.lower():
        session["score"] += 1
        feedback = f"✅ Correct! The answer is {correct_answer}."
    else:
        feedback = f"❌ Wrong — the correct answer was '{correct_answer}'."

    session["index"] += 1
    idx = session["index"]

    # More questions?
    if idx < len(_QUESTIONS):
        q = _QUESTIONS[idx]
        return {
            "bot_response": f"{feedback}\n\nQ{idx + 1}: {q['q']}",
            "session_done": False,
        }

    # Quiz complete
    score = session["score"]
    total = session["total"]
    return {
        "bot_response": f"{feedback}\n\n🏁 Quiz over! Score: {score}/{total}",
        "session_done": True,
    }


def quiz_end(state: dict) -> dict:
    """Produce the final summary."""
    sid = state.get("session_id", "")
    session = _sessions.pop(sid, {"score": 0, "total": len(_QUESTIONS)})
    return {
        "session_summary": (
            f"Session {sid}: scored {session['score']}/{session['total']}"
        ),
    }


def reset_sessions() -> None:
    """Test helper — clear all sessions."""
    _sessions.clear()
