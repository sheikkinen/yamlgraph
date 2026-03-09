"""Cross-graph session handoff utilities.

FR-168: Exports session ID from plan-judge pipeline to a well-known file,
enabling the enforce pipeline to resume the same Copilot CLI session.

The handoff uses a file-based contract (tmp/last-plan-session-id) rather than
stdout parsing or shared state, for robustness and explicit contracts.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SESSION_ID_FILENAME = "last-plan-session-id"
DEFAULT_OUTPUT_DIR = Path("tmp")


def write_session_id(
    state: dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, bool]:
    """Write judge session ID to file for cross-graph handoff.

    Extracts session_id from state["judge_result"] (CopilotResult or dict)
    and writes it to ``output_dir/last-plan-session-id``.

    Args:
        state: Graph state containing judge_result with session_id.
        output_dir: Directory to write session ID file. Defaults to ``tmp/``.

    Returns:
        State update with ``session_exported: bool``.
    """
    session_id = _extract_session_id_from_state(state)

    output_dir.mkdir(parents=True, exist_ok=True)
    session_file = output_dir / SESSION_ID_FILENAME
    session_file.write_text(session_id or "")

    exported = bool(session_id)
    if exported:
        logger.info(f"[session-handoff] Exported session ID to {session_file}")
    else:
        logger.warning("[session-handoff] No session ID found in judge_result")

    return {"session_exported": exported}


def read_session_id(input_dir: Path = DEFAULT_OUTPUT_DIR) -> str | None:
    """Read session ID from handoff file.

    Args:
        input_dir: Directory containing the session ID file.

    Returns:
        Session ID string if found and non-empty, None otherwise.
    """
    session_file = input_dir / SESSION_ID_FILENAME
    if not session_file.exists():
        return None

    content = session_file.read_text().strip()
    return content if content else None


def cleanup_session_id(input_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    """Remove session ID file after consumption.

    Prevents stale session IDs from being reused by subsequent runs.

    Args:
        input_dir: Directory containing the session ID file.
    """
    session_file = input_dir / SESSION_ID_FILENAME
    if session_file.exists():
        session_file.unlink()
        logger.info(f"[session-handoff] Cleaned up {session_file}")


def _extract_session_id_from_state(state: dict[str, Any]) -> str | None:
    """Extract session_id from judge_result in state.

    Handles both CopilotResult (Pydantic model with .session_id attribute)
    and plain dict with 'session_id' key.
    """
    judge_result = state.get("judge_result")
    if judge_result is None:
        return None

    # CopilotResult (Pydantic model) — attribute access
    if hasattr(judge_result, "session_id"):
        return judge_result.session_id

    # Dict fallback
    if isinstance(judge_result, dict):
        return judge_result.get("session_id")

    return None
