#!/usr/bin/env bash
# PostToolUse hook: run fast checks on Python files after edits.
# Checks: ruff lint, ruff format, forbidden terms, file size, debug statements.
# Returns systemMessage with all findings so the agent can self-correct.
# Audit: logs inspected tool invocations to JSONL (FR-414)
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
    'hook': 'post-edit-checks',
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

# ── Extract tool name ────────────────────────────────────────────────
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name', d.get('toolName','')))" 2>/dev/null || true)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || true)
TOOL_USE_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_use_id',''))" 2>/dev/null || true)

# Only inspect file-edit tools
case "$TOOL_NAME" in
  replace_string_in_file|create_file|multi_replace_string_in_file) ;;
  *) exit 0 ;;
esac

# ── Extract file path ────────────────────────────────────────────────
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('tool_input', d.get('toolInput', d.get('input', {})))
fp = inp.get('filePath', inp.get('file_path', ''))
if not fp:
    reps = inp.get('replacements', [])
    if reps:
        fp = reps[0].get('filePath', reps[0].get('file_path', ''))
print(fp)
" 2>/dev/null || true)

# Skip if not a Python file or file doesn't exist
if [[ ! "$FILE_PATH" == *.py ]] || [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# ── Run checks ───────────────────────────────────────────────────────
ISSUES=""

# 1. Ruff lint
if command -v ruff &>/dev/null; then
  RUFF_LINT=$(ruff check --no-fix --quiet "$FILE_PATH" 2>/dev/null || true)
  if [[ -n "$RUFF_LINT" ]]; then
    ISSUES="${ISSUES}⚠ Ruff lint errors:\n${RUFF_LINT}\n\n"
  fi
else
  audit_log "error" "ruff-missing" "$FILE_PATH"
fi

# 2. Ruff format check
if command -v ruff &>/dev/null; then
  RUFF_FMT=$(ruff format --check --quiet "$FILE_PATH" 2>&1 || true)
  if echo "$RUFF_FMT" | grep -q "would reformat\|reformatted"; then
    ISSUES="${ISSUES}⚠ Ruff format: file needs reformatting. Run: ruff format ${FILE_PATH}\n\n"
  fi
fi

# 3. Forbidden terms (TODO, FIXME, backward compatibility)
FORBIDDEN=$(grep -nE 'TODO|FIXME|backward compati(bility)?' "$FILE_PATH" 2>/dev/null || true)
if [[ -n "$FORBIDDEN" ]]; then
  ISSUES="${ISSUES}⚠ Forbidden terms found (pre-commit will reject):\n${FORBIDDEN}\n\n"
fi

# 4. File size
LINE_COUNT=$(wc -l < "$FILE_PATH" | tr -d ' ')
if [[ "$LINE_COUNT" -gt 450 ]]; then
  ISSUES="${ISSUES}✗ File size: ${LINE_COUNT} lines (max 450). Split into submodules.\n\n"
elif [[ "$LINE_COUNT" -gt 400 ]]; then
  ISSUES="${ISSUES}⚠ File size: ${LINE_COUNT} lines (target ≤400). Consider splitting.\n\n"
fi

# 5. Debug statements
DEBUG=$(grep -nE '^\s*(import pdb|from pdb import|breakpoint\(\))' "$FILE_PATH" 2>/dev/null || true)
if [[ -n "$DEBUG" ]]; then
  ISSUES="${ISSUES}⚠ Debug statements found (pre-commit will reject):\n${DEBUG}\n\n"
fi

# 6. noqa without confession (cross-reference docs/confessions.md)
NOQA_LINES=$(grep -nE '#\s*noqa' "$FILE_PATH" 2>/dev/null || true)
if [[ -n "$NOQA_LINES" ]]; then
  # Find project root (where docs/confessions.md lives)
  PROJ_ROOT=$(cd "$(dirname "$FILE_PATH")" && git rev-parse --show-toplevel 2>/dev/null || echo "")
  CONFESSIONS="${PROJ_ROOT}/docs/confessions.md"
  REL_PATH=""
  if [[ -n "$PROJ_ROOT" ]]; then
    REL_PATH="${FILE_PATH#$PROJ_ROOT/}"
  fi

  UNDOCUMENTED=""
  while IFS= read -r line; do
    LINENO_NUM=$(echo "$line" | cut -d: -f1)
    # Check if this file:line appears in confessions.md
    if [[ -f "$CONFESSIONS" ]] && [[ -n "$REL_PATH" ]]; then
      if grep -q "${REL_PATH}#L${LINENO_NUM}" "$CONFESSIONS" 2>/dev/null; then
        continue
      fi
    fi
    UNDOCUMENTED="${UNDOCUMENTED}  ${line}\n"
  done <<< "$NOQA_LINES"

  if [[ -n "$UNDOCUMENTED" ]]; then
    ISSUES="${ISSUES}⚠ noqa without confession in docs/confessions.md (pre-commit will reject):\n${UNDOCUMENTED}Add CONF-XXX entry with File, Code, Sin, and Penance.\n\n"
  fi
fi

# ── Return results ───────────────────────────────────────────────────
if [[ -z "$ISSUES" ]]; then
  audit_log "approve" "all-checks-clean" "$FILE_PATH"
  echo '{}'
  exit 0
fi

audit_log "feedback" "issues-found" "$FILE_PATH"

# Build JSON with systemMessage using python for safe escaping
python3 -c "
import json, sys
msg = sys.stdin.read().strip()
print(json.dumps({'systemMessage': msg}))
" <<< "$(echo -e "$ISSUES")"

exit 0
