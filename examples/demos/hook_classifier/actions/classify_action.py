"""Hook classifier action — domain logic for classify-and-log.

Subclasses YamlgraphAsyncAction to add:
- Classification output validation (intent, danger_level 1-5, category)
- Atomic JSONL log appending
- Session history accumulation with FIFO eviction
- Deterministic fallback on error/timeout
- Reason code mapping

Discovered by ActionLoader via --actions-dir (classify_action.py → type: classify).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from yamlgraph.utils.fsm import YamlgraphAsyncAction as _SharedYamlgraphAsyncAction
from yamlgraph.utils.fsm.snapshot import SnapshotParams

logger = logging.getLogger(__name__)

GRAPH_BASE = Path(__file__).resolve().parent.parent

MAX_HISTORY = 50
HISTORY_WINDOW_SECONDS = 30 * 60  # 30 minutes
MAX_DETAIL_LEN = 500
MAX_ENTRY_BYTES = 4096

VALID_INTENTS = frozenset({"legitimate", "suspicious", "hostile"})
VALID_CATEGORIES = frozenset(
    {
        "normal",
        "exfiltration",
        "injection",
        "evasion",
        "self-modification",
        "credential-harvest",
    }
)

FALLBACK = {
    "intent": "unknown",
    "danger_level": 1,
    "category": "error",
    "reasoning": "",
}


def validate_classification(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize classification output.

    Enforces: intent in {legitimate, suspicious, hostile},
    danger_level int 1-5 (never 0), category in valid set.
    """
    result = dict(raw)

    if result.get("intent") not in VALID_INTENTS:
        result["intent"] = "unknown"

    dl = result.get("danger_level")
    if not isinstance(dl, int) or dl < 1 or dl > 5:
        result["danger_level"] = 1

    if result.get("category") not in VALID_CATEGORIES:
        result["category"] = "normal"

    if not isinstance(result.get("reasoning"), str):
        result["reasoning"] = ""

    return result


def reason_code(classification: dict[str, Any]) -> str:
    """Map classification intent to audit reason code."""
    intent = classification.get("intent", "unknown")
    if intent in VALID_INTENTS:
        return f"classified-{intent}"
    return "classify-error"


def format_detail(classification: dict[str, Any]) -> str:
    """Format classification as compact detail string, capped at MAX_DETAIL_LEN."""
    parts = [
        f"danger={classification.get('danger_level', '?')}",
        f"category={classification.get('category', '?')}",
        f"intent={classification.get('intent', '?')}",
        f"reasoning={classification.get('reasoning', '')}",
    ]
    detail = " ".join(parts)
    return detail[:MAX_DETAIL_LEN]


def append_entry(log_path: Path, entry: dict[str, Any]) -> None:
    """Append a single JSONL entry atomically.

    Uses open(mode='a') and print(..., flush=True) for single write() syscall.
    Truncates detail if serialized entry exceeds PIPE_BUF (4096 bytes).
    """
    line = json.dumps(entry, ensure_ascii=True)
    if len(line.encode("utf-8")) > MAX_ENTRY_BYTES and "detail" in entry:
        # Truncate detail to fit within PIPE_BUF
        overflow = len(line.encode("utf-8")) - MAX_ENTRY_BYTES
        entry["detail"] = (
            entry["detail"][: max(0, len(entry["detail"]) - overflow - 10)] + "..."
        )
        line = json.dumps(entry, ensure_ascii=True)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        print(line, file=f, flush=True)


def evict_history(
    history: list[dict[str, Any]],
    max_entries: int = MAX_HISTORY,
    window_seconds: int = HISTORY_WINDOW_SECONDS,
) -> list[dict[str, Any]]:
    """FIFO eviction: cap entries and drop old timestamps."""
    if len(history) > max_entries:
        history = history[-max_entries:]

    cutoff = datetime.now(UTC).timestamp() - window_seconds
    return [e for e in history if _parse_ts(e.get("ts", "")) >= cutoff]


def _parse_ts(ts_str: str) -> float:
    """Parse ISO timestamp to epoch float. Returns 0 on failure."""
    if not ts_str:
        return 0.0
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return 0.0


class ClassifyAction(_SharedYamlgraphAsyncAction):
    """Hook classification action — validates, logs, and accumulates history."""

    GRAPH_BASE_DIR = GRAPH_BASE

    def _log_path(self, context: dict[str, Any]) -> Path:
        """Resolve log path from FSM context or default."""
        rel = context.get("log_path", "logs/classifications.jsonl")
        p = Path(rel)
        if p.is_absolute():
            return p
        return GRAPH_BASE / rel

    def on_launch(self, snap: SnapshotParams, context: dict[str, Any]) -> None:
        """Inject session history into graph variables before execution."""
        payload = context.get("_last_payload", {})
        session_id = payload.get("session_id", "unknown")

        # Get per-session history from FSM context
        all_history = context.get("session_history", [])
        session_entries = [e for e in all_history if e.get("session_id") == session_id]

        # Inject into graph variables via snapshot
        if snap.initial_state:
            snap.initial_state["session_history"] = session_entries
            snap.initial_state["tool_name"] = payload.get("tool", "unknown")
            snap.initial_state["command"] = str(payload.get("command", ""))[:500]

    def on_success(
        self,
        snap: SnapshotParams | None,
        event: str,
        elapsed_ms: int,
        context: dict[str, Any] | None,
    ) -> None:
        """Validate classification, append to log, update session history."""
        if context is None:
            return

        payload = context.get("_last_payload", {})
        output_key = snap.output_key if snap else "classification"
        raw_classification = context.get(output_key, {})

        classification = validate_classification(raw_classification)
        code = reason_code(classification)
        tool = payload.get("tool", "unknown")
        session_id = payload.get("session_id", "unknown")

        entry = {
            "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "hook": "hook-classifier",
            "tool": tool,
            "decision": "classified",
            "reason": code,
            "detail": format_detail(classification),
            "session_id": session_id,
        }
        append_entry(self._log_path(context), entry)

        # Update session history in FSM context
        history = list(context.get("session_history", []))
        history.append(
            {
                "ts": payload.get("ts", entry["ts"]),
                "tool": tool,
                "command": str(payload.get("command", ""))[:100],
                "session_id": session_id,
                "classification": {
                    "intent": classification["intent"],
                    "danger_level": classification["danger_level"],
                },
            }
        )
        context["session_history"] = evict_history(history)
        context["classification_count"] = context.get("classification_count", 0) + 1

        logger.info(
            "Classified: tool=%s intent=%s danger=%s (%dms)",
            tool,
            classification["intent"],
            classification["danger_level"],
            elapsed_ms,
        )

    def on_error(
        self,
        snap: SnapshotParams | None,
        exc: Exception,
        elapsed_ms: int,
        context: dict[str, Any] | None,
    ) -> None:
        """Write deterministic fallback on classification failure."""
        if context is None:
            return

        payload = context.get("_last_payload", {})
        tool = payload.get("tool", "unknown")
        session_id = payload.get("session_id", "unknown")

        fallback = {**FALLBACK, "reasoning": str(exc)[:400]}
        code = "classify-timeout" if "timeout" in str(exc).lower() else "classify-error"

        entry = {
            "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "hook": "hook-classifier",
            "tool": tool,
            "decision": "classified",
            "reason": code,
            "detail": format_detail(fallback),
            "session_id": session_id,
        }
        append_entry(self._log_path(context), entry)

        logger.warning(
            "Classification failed: tool=%s reason=%s (%dms): %s",
            tool,
            code,
            elapsed_ms,
            exc,
        )
