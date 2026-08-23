#!/usr/bin/env bash
# PreToolUse hook: block dangerous terminal patterns (ramp Tier-1 curated
# guard — see ramp/curation-diffs.md#pre-command-guard in the source repo).
# 1. Co-authored-by trailers in commits/merges/file writes
# 2. --no-verify flag (safety bypass forbidden)
# 3. Multiline git commit -m (use git commit -F ./tmp/msg.txt instead)
# 4. pytest piped to head/tail without tee (output buffering)
# Audit: logs every tool invocation to JSONL.
set -euo pipefail

INPUT=$(cat)

# ── Audit log helper ─────────────────────────────────────────────────
LOG_DIR="${HOOK_LOG_DIR:-$(dirname "$0")/../logs}"
SESSION_ID=""
TOOL_USE_ID=""

audit_log() {
  # args: decision reason detail
  local decision="$1" reason="$2" detail="$3"
  mkdir -p "$LOG_DIR" 2>/dev/null || return 0
  python3 -c "
import json, sys, datetime as dt
entry = {
    'ts': dt.datetime.now(dt.timezone.utc).isoformat(),
    'hook': 'pre-command-guard',
    'tool': sys.argv[1],
    'decision': sys.argv[2],
    'reason': sys.argv[3],
    'detail': sys.argv[4][:500]
}
if sys.argv[5]: entry['session_id'] = sys.argv[5]
if sys.argv[6]: entry['tool_use_id'] = sys.argv[6]
print(json.dumps(entry))
" "${TOOL_NAME:-unknown}" "$decision" "$reason" "$detail" "$SESSION_ID" "$TOOL_USE_ID" >> "$LOG_DIR/audit.jsonl" 2>/dev/null || true
}

emit_deny() {
  local reason_text="$1"
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$reason_text"
  }
}
EOF
}

# ── Parse input (fail-closed) ────────────────────────────────────────
parse_hook_input() {
  python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', d.get('toolInput', d.get('input', {})))
    tool = d.get('tool_name', d.get('toolName', ''))
    cmd = inp.get('command', '') if isinstance(inp, dict) else ''
    detail = json.dumps(inp)[:500] if inp else '{}'
    sid = d.get('session_id', '')
    tuid = d.get('tool_use_id', '')
    for value in (tool, cmd, detail, sid, tuid):
        sys.stdout.write(value if isinstance(value, str) else str(value))
        sys.stdout.write('\0')
except Exception:
    sys.exit(1)
"
}

if ! {
  IFS= read -r -d '' TOOL_NAME &&
  IFS= read -r -d '' COMMAND &&
  IFS= read -r -d '' DETAIL &&
  IFS= read -r -d '' SESSION_ID &&
  IFS= read -r -d '' TOOL_USE_ID
} < <(printf '%s' "$INPUT" | parse_hook_input 2>/dev/null); then
  TOOL_NAME="unknown"
  audit_log "deny" "parse-error" "JSON parse failed"
  emit_deny "Hook cannot parse input — denying for safety."
  exit 0
fi

# Only inspect terminal tool calls
if [[ "$TOOL_NAME" != "run_in_terminal" && "$TOOL_NAME" != "send_to_terminal" ]]; then
  audit_log "pass" "not-inspected" "$DETAIL"
  echo '{"decision":"approve"}'
  exit 0
fi

# ── Check 1: Co-authored-by trailers ─────────────────────────────────
IS_COMMIT_CMD=false
if echo "$COMMAND" | grep -qiE '(git\s+commit|git\s+merge|>>?\s*.*msg|>>?\s*.*commit)'; then
  IS_COMMIT_CMD=true
fi
if echo "$COMMAND" | grep -qiE '(echo|printf|cat\s*<<).*co-authored-by'; then
  IS_COMMIT_CMD=true
fi
if [[ "$IS_COMMIT_CMD" == "true" ]] && echo "$COMMAND" | grep -qi 'co-authored-by'; then
  audit_log "deny" "co-authored-by" "${COMMAND:0:200}"
  emit_deny "Co-authored-by trailers are forbidden. Remove the trailer before committing."
  exit 0
fi

# ── Check 2: --no-verify bypass ──────────────────────────────────────
if echo "$COMMAND" | grep -qE '(git\s+(commit|push|merge|rebase)|pre-commit)\b' && \
   echo "$COMMAND" | grep -q '\-\-no-verify'; then
  audit_log "deny" "no-verify" "${COMMAND:0:200}"
  emit_deny "--no-verify is forbidden. Remove the flag and let hooks run."
  exit 0
fi

# ── Check 3: multiline git commit -m ─────────────────────────────────
if echo "$COMMAND" | head -1 | grep -qE 'git\s+commit\s+.*-m\s'; then
  LINE_COUNT=$(echo "$COMMAND" | wc -l | tr -d ' ')
  if [[ "$LINE_COUNT" -gt 1 ]]; then
    audit_log "deny" "multiline-m" "${COMMAND:0:200}"
    emit_deny "Multiline git commit -m triggers dquote shell trap. Write message to ./tmp/msg.txt and use: git commit -F ./tmp/msg.txt"
    exit 0
  fi
fi

# ── Check 4: pytest piped to head/tail without tee ───────────────────
if echo "$COMMAND" | grep -qE 'pytest\b' && \
   echo "$COMMAND" | grep -qE '\|\s*(head|tail)\b' && \
   ! echo "$COMMAND" | grep -qE '\|\s*tee\b'; then
  audit_log "deny" "pipe-buffer" "${COMMAND:0:200}"
  emit_deny "pytest piped to head/tail buffers all output until exit — hangs and failures are invisible.\\n\\nUse tee for streaming:\\n  pytest ... 2>&1 | tee logs/run.log"
  exit 0
fi

audit_log "approve" "clean" "${COMMAND:0:200}"
echo '{"decision":"approve"}'
exit 0
