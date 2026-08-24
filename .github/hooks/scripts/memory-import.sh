#!/bin/sh
# FR-874: SessionStart memory import — fail-open, but never silent (judgement R-4).
# A broken sync must not block a session; a failure leaves one bounded
# JSONL audit record instead of masquerading as a successful import.
REPO="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)" || exit 0
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)" || exit 0
LOG="${MEMORY_SYNC_LOG:-$REPO/.github/hooks/logs/memory-sync.jsonl}"

set -- import --quiet
[ -n "$MEMORY_SYNC_ROOT" ] && set -- "$@" --memory-root "$MEMORY_SYNC_ROOT"
[ -n "$MEMORY_SYNC_STORE" ] && set -- "$@" --store "$MEMORY_SYNC_STORE"

if command -v timeout >/dev/null 2>&1; then
  timeout 8 "$PY" "$REPO/scripts/memory_sync.py" "$@" 2>/dev/null
else
  "$PY" "$REPO/scripts/memory_sync.py" "$@" 2>/dev/null
fi
rc=$?

if [ "$rc" -ne 0 ]; then
  mkdir -p "$(dirname "$LOG")" 2>/dev/null
  printf '{"ts":"%s","event":"memory_sync_import_failed","rc":%d}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" >> "$LOG" 2>/dev/null
  # bounded evidence: keep only the most recent 200 records
  if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 200 ]; then
    tail -200 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
  fi
fi
exit 0
