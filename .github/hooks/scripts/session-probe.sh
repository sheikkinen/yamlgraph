#!/bin/sh
# FR-743 AC-00: platform-contract probe — do SessionStart /
# UserPromptSubmit / SessionEnd fire, what arrives on stdin, and is
# stdout agent-visible? One line to audit.jsonl per firing; a marker
# on stdout to test visibility. Fail-open everywhere.
REPO="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)" || exit 0
LOG="$REPO/.github/hooks/logs/audit.jsonl"
mkdir -p "$(dirname "$LOG")" 2>/dev/null
STDIN=$(cat 2>/dev/null | head -c 4000)
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
if [ -n "$PY" ]; then
  "$PY" - "$STDIN" >> "$LOG" 2>/dev/null <<'EOF' || true
import json, sys, datetime
raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    data = json.loads(raw) if raw else {}
except ValueError:
    data = {"unparsed": raw[:200]}
print(json.dumps({
    "ts": datetime.datetime.utcnow().isoformat() + "Z",
    "probe": "FR-743",
    "hook_event_name": data.get("hook_event_name", "?"),
    "session_id": data.get("session_id", "?"),
    "stdin_keys": sorted(data.keys()),
}))
EOF
fi
# stdout visibility marker (AC-00: where does this land?)
echo "FR-743 probe: hook event fired (see .github/hooks/logs/audit.jsonl)"
exit 0
