#!/usr/bin/env bash
# PreToolUse hook: block dangerous terminal patterns.
# 1. Co-authored-by trailers in commits/merges/file writes
# 2. --no-verify flag (safety bypass forbidden by Scripture)
# 3. Multiline git commit -m (use git commit -F ./tmp/msg.txt instead)
# Audit: logs every tool invocation to JSONL (FR-414)
set -euo pipefail

INPUT=$(cat)

# ── Audit log helper ─────────────────────────────────────────────────
LOG_DIR="${HOOK_LOG_DIR:-$(dirname "$0")/../logs}"

audit_log() {
  # args: decision reason detail
  local decision="$1" reason="$2" detail="$3"
  mkdir -p "$LOG_DIR" 2>/dev/null || return 0
  python3 -c "
import json, sys, datetime as dt
print(json.dumps({
    'ts': dt.datetime.now(dt.timezone.utc).isoformat(),
    'hook': 'pre-command-guard',
    'tool': sys.argv[1],
    'decision': sys.argv[2],
    'reason': sys.argv[3],
    'detail': sys.argv[4][:200]
}))
" "${TOOL_NAME:-unknown}" "$decision" "$reason" "$detail" >> "$LOG_DIR/audit.jsonl" 2>/dev/null || true
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
PARSED=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', d.get('toolInput', d.get('input', {})))
    tool = d.get('tool_name', d.get('toolName', ''))
    cmd = inp.get('command', '') if isinstance(inp, dict) else ''
    detail = json.dumps(inp)[:200] if inp else '{}'
    print(json.dumps({'tool': tool, 'command': cmd, 'detail': detail}))
except Exception:
    sys.exit(1)
" 2>/dev/null) || {
  TOOL_NAME="unknown"
  audit_log "deny" "parse-error" "JSON parse failed"
  emit_deny "Hook cannot parse input — denying for safety."
  exit 0
}

TOOL_NAME=$(echo "$PARSED" | python3 -c "import sys,json; print(json.load(sys.stdin)['tool'])")
COMMAND=$(echo "$PARSED" | python3 -c "import sys,json; print(json.load(sys.stdin)['command'])")
DETAIL=$(echo "$PARSED" | python3 -c "import sys,json; print(json.load(sys.stdin)['detail'])")

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

audit_log "approve" "clean" "${COMMAND:0:200}"
echo '{"decision":"approve"}'
exit 0
