#!/usr/bin/env python3
"""Session Timeline Join — merges audit.jsonl and VS Code transcript JSONL.

Joins tool invocations (audit) with user prompts (transcript) by session_id
and timestamp. Produces a human-readable session narrative or JSON output.

Usage:
    python3 session-timeline.py --audit path/to/audit.jsonl
    python3 session-timeline.py --audit audit.jsonl --transcript path/to/transcript.jsonl
    python3 session-timeline.py --audit audit.jsonl --session <uuid> --json
    python3 session-timeline.py --audit audit.jsonl --filter deny
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def parse_ts(raw: str) -> datetime:
    """Normalize Python (+00:00) and JS (Z) ISO timestamps to aware UTC."""
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(UTC)


def load_jsonl(path: Path) -> list[dict]:
    """Read JSONL file, skip blank/malformed lines."""
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def detect_session(audit: list[dict]) -> str | None:
    """Return most recent session_id from audit entries."""
    for entry in reversed(audit):
        sid = entry.get("session_id")
        if sid:
            return sid
    return None


def discover_transcript(session_id: str) -> Path | None:
    """Try to find transcript JSONL in VS Code workspace storage."""
    base = (
        Path.home()
        / "Library"
        / "Application Support"
        / "Code"
        / "User"
        / "workspaceStorage"
    )
    if not base.is_dir():
        return None
    for workspace_dir in base.iterdir():
        transcript = (
            workspace_dir
            / "GitHub.copilot-chat"
            / "transcripts"
            / f"{session_id}.jsonl"
        )
        if transcript.is_file():
            return transcript
    return None


def build_timeline(
    audit: list[dict],
    user_messages: list[dict],
) -> list[dict]:
    """Join audit entries to nearest preceding user message by timestamp.

    Returns list of dicts with keys: ts, tool, decision, reason, detail,
    user_prompt (str|None), user_ts (str|None).
    """
    # Parse and sort user messages by timestamp
    um_sorted = []
    for msg in user_messages:
        ts_raw = msg.get("timestamp", "")
        content = ""
        data = msg.get("data", {})
        if isinstance(data, dict):
            content = data.get("content", "")
        try:
            um_sorted.append((parse_ts(ts_raw), content, ts_raw))
        except (ValueError, TypeError):
            continue
    um_sorted.sort(key=lambda x: x[0])

    # Parse and sort audit entries
    audit_sorted = []
    for entry in audit:
        try:
            ts = parse_ts(entry["ts"])
            audit_sorted.append((ts, entry))
        except (ValueError, TypeError, KeyError):
            continue
    audit_sorted.sort(key=lambda x: x[0])

    timeline = []
    for audit_ts, entry in audit_sorted:
        # Find nearest preceding user message
        user_prompt = None
        user_ts = None
        for um_ts, content, raw_ts in reversed(um_sorted):
            if um_ts <= audit_ts:
                user_prompt = content
                user_ts = raw_ts
                break

        timeline.append(
            {
                "ts": entry["ts"],
                "tool": entry.get("tool", ""),
                "decision": entry.get("decision", ""),
                "reason": entry.get("reason", ""),
                "detail": entry.get("detail", ""),
                "session_id": entry.get("session_id", ""),
                "user_prompt": user_prompt,
                "user_ts": user_ts,
            }
        )

    return timeline


def render_human(timeline: list[dict]) -> str:
    """Render timeline as human-readable grouped output."""
    if not timeline:
        return "No entries."

    session_id = timeline[0].get("session_id", "unknown")
    lines = [f"Session: {session_id}", ""]

    current_prompt = None
    counts = {}
    for entry in timeline:
        prompt = entry.get("user_prompt")
        prompt_ts = entry.get("user_ts")

        # New group header when user prompt changes
        if prompt != current_prompt:
            current_prompt = prompt
            if prompt:
                ts_display = ""
                if prompt_ts:
                    try:
                        ts_display = parse_ts(prompt_ts).strftime("%H:%M:%S")
                    except (ValueError, TypeError):
                        ts_display = "??:??:??"
                truncated = prompt[:80] + ("..." if len(prompt) > 80 else "")
                lines.append(f'[{ts_display}] USER: "{truncated}"')
            else:
                lines.append("[--:--:--] (no user prompt)")

        # Tool line
        ts_display = ""
        try:
            ts_display = parse_ts(entry["ts"]).strftime("%H:%M:%S")
        except (ValueError, TypeError):
            ts_display = "??:??:??"

        decision = (
            entry["decision"].upper()
            if entry["decision"] == "deny"
            else entry["decision"]
        )
        tool = entry["tool"]
        reason = entry["reason"]
        detail = entry.get("detail", "")
        # Truncate detail for display
        if len(detail) > 60:
            detail = detail[:57] + "..."

        lines.append(
            f"  [{ts_display}] {tool:<20s} {decision:<8s} {reason:<20s} {detail}"
        )

        counts[entry["decision"]] = counts.get(entry["decision"], 0) + 1

    # Summary
    total = sum(counts.values())
    parts = [f"{total} tool calls"]
    for k in ("approve", "pass", "feedback", "deny", "error"):
        if k in counts:
            parts.append(f"{counts[k]} {k}")
    lines.append("")
    lines.append(f"Summary: {', '.join(parts)}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Session timeline join")
    parser.add_argument("--audit", required=True, help="Path to audit.jsonl")
    parser.add_argument("--transcript", help="Path to transcript JSONL (explicit)")
    parser.add_argument("--session", help="Session ID (default: most recent)")
    parser.add_argument(
        "--json", action="store_true", dest="json_out", help="JSON output"
    )
    parser.add_argument(
        "--filter",
        dest="decision_filter",
        help="Show only this decision (deny, feedback, etc.)",
    )
    args = parser.parse_args()

    audit_path = Path(args.audit)
    if not audit_path.is_file():
        print(f"error: audit file not found: {audit_path}", file=sys.stderr)
        return 1

    all_audit = load_jsonl(audit_path)

    # Determine session
    session_id = args.session or detect_session(all_audit)

    # Filter audit by session
    if session_id:
        audit = [e for e in all_audit if e.get("session_id") == session_id]
    else:
        audit = all_audit

    # Load transcript
    user_messages = []
    transcript_path = None
    if args.transcript:
        transcript_path = Path(args.transcript)
    elif session_id:
        transcript_path = discover_transcript(session_id)

    if transcript_path and transcript_path.is_file():
        all_transcript = load_jsonl(transcript_path)
        user_messages = [e for e in all_transcript if e.get("type") == "user.message"]

    # Build timeline
    timeline = build_timeline(audit, user_messages)

    # Apply filter
    if args.decision_filter:
        timeline = [e for e in timeline if e["decision"] == args.decision_filter]

    # Output
    if args.json_out:
        print(json.dumps(timeline, indent=2))
    else:
        print(render_human(timeline))

    return 0


if __name__ == "__main__":
    sys.exit(main())
