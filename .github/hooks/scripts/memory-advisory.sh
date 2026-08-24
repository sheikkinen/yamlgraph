#!/bin/sh
# FR-877: memory-curation staleness advisory — fail-open, never silent-success.
# Prints the advisory line (if any) into the session briefing; a failure
# leaves one bounded JSONL record instead of masquerading as no-drift.
REPO="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)" || exit 0
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)" || exit 0
LOG="${MEMORY_ADVISORY_LOG:-$REPO/.github/hooks/logs/memory-advisory.jsonl}"
THRESHOLD="${MEMORY_ADVISORY_THRESHOLD:-5}"
ROOT="${MEMORY_ADVISORY_ROOT:-}"

if [ -z "$ROOT" ]; then
  WS="$HOME/Library/Application Support/Code/User/workspaceStorage"
  ROOT="$(grep -l "$(basename "$REPO")" "$WS"/*/workspace.json 2>/dev/null \
    | head -1 | xargs -I{} dirname {} 2>/dev/null)/GitHub.copilot-chat/memory-tool/memories"
fi

if command -v timeout >/dev/null 2>&1; then
  timeout "${MEMORY_ADVISORY_TIMEOUT:-5}" "$PY" \
    "$REPO/examples/memory-curation/advisory.py" \
    --memory-root "$ROOT" --threshold "$THRESHOLD" 2>/dev/null
else
  "$PY" "$REPO/examples/memory-curation/advisory.py" \
    --memory-root "$ROOT" --threshold "$THRESHOLD" 2>/dev/null
fi
rc=$?

if [ "$rc" -ne 0 ]; then
  mkdir -p "$(dirname "$LOG")" 2>/dev/null
  printf '{"ts":"%s","event":"memory_advisory_failed","rc":%d}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" >> "$LOG" 2>/dev/null
  if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 200 ]; then
    tail -200 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
  fi
fi
exit 0
