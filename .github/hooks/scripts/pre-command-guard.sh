#!/usr/bin/env bash
# PreToolUse hook: block dangerous terminal patterns.
# 1. Co-authored-by trailers in commits/merges/file writes
# 2. --no-verify flag (safety bypass forbidden by Scripture)
# 3. Multiline git commit -m (use git commit -F ./tmp/msg.txt instead)
# 4. pytest piped to head/tail without tee (output buffering) (FR-440)
# Audit: logs every tool invocation to JSONL (FR-414)
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

# ── Lockdown check ───────────────────────────────────────────────────
LOCKFILE="$LOG_DIR/.lockdown"
if [[ -f "$LOCKFILE" ]]; then
  # Allow only unlock command through
  if [[ "$TOOL_NAME" == "run_in_terminal" || "$TOOL_NAME" == "send_to_terminal" ]] && \
     echo "$COMMAND" | grep -q '\.github/hooks/cmd unlock'; then
    : # fall through to lockdown command handler
  else
    audit_log "deny" "lockdown-active" "$DETAIL"
    emit_deny "LOCKDOWN ACTIVE. All tool calls blocked. User must issue: .github/hooks/cmd unlock"
    exit 0
  fi
fi

# ── Reasoning pattern sentinel check (FR-438, renamed in FR-439) ─────
TC_SENTINEL="$LOG_DIR/.reasoning-flag-$SESSION_ID"
if [[ -n "$SESSION_ID" && -f "$TC_SENTINEL" ]]; then
  TC_DATA=$(cat "$TC_SENTINEL" 2>/dev/null || echo '{}')
  TC_PHRASE=$(echo "$TC_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('phrase',''))" 2>/dev/null || echo "unknown")
  TC_DOCTRINE=$(echo "$TC_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('doctrine',''))" 2>/dev/null || echo "")
  rm -f "$TC_SENTINEL"
  audit_log "deny" "reasoning-pattern" "phrase=$TC_PHRASE"
  emit_deny "⚠ Reasoning pattern flagged\\n\\nFlagged phrase: \\\"$TC_PHRASE\\\"\\n\\nDoctrine: $TC_DOCTRINE\\n\\nThis denial is one-shot. Your next tool call will proceed."
  exit 0
fi

# ── Lockdown command channel ─────────────────────────────────────────
if [[ "$TOOL_NAME" == "run_in_terminal" || "$TOOL_NAME" == "send_to_terminal" ]] && \
   echo "$COMMAND" | grep -q '^\.github/hooks/cmd '; then
  HOOKCTL_CMD=$(echo "$COMMAND" | sed 's/^\.github\/hooks\/cmd //')
  case "$HOOKCTL_CMD" in
    lockdown)
      touch "$LOCKFILE"
      audit_log "deny" "lockdown-set" "lockdown activated"
      emit_deny "Lockdown active — all tool calls will be denied until: .github/hooks/cmd unlock"
      ;;
    unlock)
      rm -f "$LOCKFILE"
      audit_log "deny" "lockdown-clear" "lockdown deactivated"
      emit_deny "Lockdown lifted. Normal operations resumed."
      ;;
    status)
      SUMMARY=$(python3 -c "
import json, collections, pathlib
logfile = pathlib.Path('$LOG_DIR') / 'audit.jsonl'
if not logfile.exists():
    print('No audit log found.')
else:
    lines = logfile.read_text().strip().splitlines()
    decisions = collections.Counter()
    tools = collections.Counter()
    for line in lines:
        d = json.loads(line)
        decisions[d.get('decision','')] += 1
        tools[d.get('tool','')] += 1
    total = sum(decisions.values())
    dec_str = ', '.join(f'{k}={v}' for k,v in decisions.most_common())
    tool_str = ', '.join(f'{k}={v}' for k,v in tools.most_common(5))
    lockdown = 'YES' if pathlib.Path('$LOCKFILE').exists() else 'no'
    print(f'Audit: {total} total entries. Decisions: {dec_str}. Top tools: {tool_str}. Lockdown: {lockdown}')
" 2>/dev/null)
      audit_log "deny" "lockdown-status" "status requested"
      emit_deny "$SUMMARY"
      ;;
    *)
      audit_log "deny" "lockdown-unknown" "unknown cmd: $HOOKCTL_CMD"
      emit_deny "Unknown command: $HOOKCTL_CMD. Available: lockdown, unlock, status"
      ;;
  esac
  exit 0
fi

# Only inspect run_in_terminal / send_to_terminal tool calls
if [[ "$TOOL_NAME" != "run_in_terminal" && "$TOOL_NAME" != "send_to_terminal" ]]; then
  audit_log "pass" "not-inspected" "$DETAIL"
  echo '{"decision":"approve"}'
  exit 0
fi

# Only block when the command is constructing a commit (git commit, writing msg files)
# Allow legitimate searches (grep, rg, cat, etc.) that merely reference the text
IS_COMMIT_CMD=false
if echo "$COMMAND" | grep -qiE '(git\s+commit|git\s+merge|>>?\s*.*msg|>>?\s*.*commit)'; then
  IS_COMMIT_CMD=true
fi

# Also block echo/printf/cat heredoc piping into files (writing trailer to a file)
if echo "$COMMAND" | grep -qiE '(echo|printf|cat\s*<<).*co-authored-by'; then
  IS_COMMIT_CMD=true
fi

if [[ "$IS_COMMIT_CMD" == "true" ]] && echo "$COMMAND" | grep -qi 'co-authored-by'; then
  audit_log "deny" "co-authored-by" "${COMMAND:0:200}"
  emit_deny "Co-authored-by trailers are forbidden. CI (copilot-trailer-gate) and pre-commit (block-ai-coauthor) will reject them. Remove the trailer before committing."
  exit 0
fi

# ── Check 2: --no-verify bypass ──────────────────────────────────────
# Block git/pre-commit commands using --no-verify. Allow grep/echo that mention it.
if echo "$COMMAND" | grep -qE '(git\s+(commit|push|merge|rebase)|pre-commit)\b' && \
   echo "$COMMAND" | grep -q '\-\-no-verify'; then
  audit_log "deny" "no-verify" "${COMMAND:0:200}"
  emit_deny "--no-verify is forbidden. Scripture: '[--no-verify flag will result in immediate termination]'. Remove the flag and let hooks run."
  exit 0
fi

# ── Check 3: multiline git commit -m ─────────────────────────────────
# Block git commit -m with newlines (causes dquote shell trap).
# Guide: write to ./tmp/msg.txt and use git commit -F ./tmp/msg.txt
# After JSON parsing, \n becomes actual newlines, so check line count.
if echo "$COMMAND" | head -1 | grep -qE 'git\s+commit\s+.*-m\s'; then
  LINE_COUNT=$(echo "$COMMAND" | wc -l | tr -d ' ')
  if [[ "$LINE_COUNT" -gt 1 ]]; then
  audit_log "deny" "multiline-m" "${COMMAND:0:200}"
  emit_deny "Multiline git commit -m triggers dquote shell trap. Write message to ./tmp/msg.txt and use: git commit -F ./tmp/msg.txt"
    exit 0
  fi
fi

# ── Check 4: pytest piped to head/tail without tee ───────────────────
# pytest output piped directly to head/tail buffers everything → agent
# sees no output until pytest exits, masking hangs and slow tests.
# Require tee for streaming: pytest ... 2>&1 | tee logs/run.log
if echo "$COMMAND" | grep -qE 'pytest\b' && \
   echo "$COMMAND" | grep -qE '\|\s*(head|tail)\b' && \
   ! echo "$COMMAND" | grep -qE '\|\s*tee\b'; then
  audit_log "deny" "pipe-buffer" "${COMMAND:0:200}"
  emit_deny "pytest piped to head/tail buffers all output until exit — hangs and failures are invisible.\\n\\nUse tee for streaming:\\n  pytest ... 2>&1 | tee logs/run.log\\n\\nThen inspect separately:\\n  tail -20 logs/run.log"
  exit 0
fi

audit_log "approve" "clean" "${COMMAND:0:200}"
echo '{"decision":"approve"}'
exit 0
