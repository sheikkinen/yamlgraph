#!/usr/bin/env bash
# FR-902 SessionStart hook: create/adopt this session's git worktree lane.
#
# Live-gated (AC-13/C-2): a silent no-op unless the live flag file exists.
# The operator arms the flag only after reviewing the enforcement diff —
# hook rollout is never live policy by merge alone.
#
# Contract (R-3): hook JSON arrives on stdin (same as session-probe.sh);
# session_id must be a full UUID-shaped path segment; refusals exit
# non-zero with an audit entry. Lane creation is delegated to
# scripts/worktree.sh session (R-2) — one substrate, no setup drift.
set -uo pipefail

HOOK_REPO="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd -P)" || exit 0
REPO="${FR902_REPO:-$HOOK_REPO}"
LOG_DIR="${HOOK_LOG_DIR:-$HOOK_REPO/.github/hooks/logs}"
WORKTREE_SH="${FR902_WORKTREE_SH:-$HOOK_REPO/scripts/worktree.sh}"
LIVE_FLAG="${FR902_LIVE_FLAG:-$REPO/.github/hooks/fr902.live}"

STDIN=$(cat 2>/dev/null)
SID=""

audit() { # decision reason
    mkdir -p "$LOG_DIR" 2>/dev/null
    printf '{"ts":"%s","hook":"session-worktree","decision":"%s","reason":"%s","session_id":"%s"}\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" "$SID" \
        >>"$LOG_DIR/audit.jsonl" 2>/dev/null
}

# not live: no lane, no record, no denial class downstream
[[ -f "$LIVE_FLAG" ]] || exit 0

SID=$(printf '%s' "$STDIN" | python3 -c \
    "import json,sys; print(json.load(sys.stdin).get('session_id',''))" \
    2>/dev/null) || SID=""

if ! printf '%s' "$SID" | grep -qE \
    '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'; then
    audit "reject" "invalid session id"
    exit 1
fi

LANE=$(cd "$REPO" && "$WORKTREE_SH" session "$SID" 2>/dev/null | tail -1)
if [[ -z "$LANE" || ! -d "$LANE" ]]; then
    audit "reject" "lane creation failed"
    exit 1
fi

mkdir -p "$LOG_DIR/session-lanes" 2>/dev/null
printf '{"session_id":"%s","branch":"session/%s","lane":"%s"}\n' \
    "$SID" "$SID" "$LANE" >"$LOG_DIR/session-lanes/$SID.json"
audit "approve" "lane ready"
# FR-925: agent-visible lane delivery via the structured JSON channel;
# plain stdout is captured into hook telemetry and never reaches context.
python3 - "$LANE" <<'PYEOF'
import json
import sys

lane = sys.argv[1]
ctx = "FR-902 session lane: %s\nWork there: cd '%s'" % (lane, lane)
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart", "additionalContext": ctx}}))
PYEOF
exit 0
