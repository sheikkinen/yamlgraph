#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="${HOOK_LOG_DIR:-$(dirname "$0")/../../logs}"
TOOL_NAME=""
SESSION_ID=""
TOOL_USE_ID=""
FILE_PATHS=()

is_edit_tool() {
  case "$1" in
    replace_string_in_file|create_file|multi_replace_string_in_file|apply_patch) return 0 ;;
    *) return 1 ;;
  esac
}

parse_tool_input() {
  local input="$1"

  TOOL_NAME=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name', d.get('toolName','')))" 2>/dev/null || true)
  SESSION_ID=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || true)
  TOOL_USE_ID=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_use_id',''))" 2>/dev/null || true)

  FILE_PATHS=()
  while IFS= read -r line; do
    if [[ -n "$line" ]]; then
      FILE_PATHS+=("$line")
    fi
  done < <(echo "$input" | python3 -c "
import sys
import json

d = json.load(sys.stdin)
inp = d.get('tool_input', d.get('toolInput', d.get('input', {})))
tool_name = d.get('tool_name', d.get('toolName', ''))

if tool_name == 'apply_patch':
    patch_text = inp.get('input', '')
    files = []
    for line in patch_text.splitlines():
        if line.startswith('*** Add File: ') or line.startswith('*** Update File: '):
            files.append(line.split(': ', 1)[1].strip())
    seen = set()
    for file_path in files:
        if file_path and file_path not in seen:
            seen.add(file_path)
            print(file_path)
else:
    fp = inp.get('filePath', inp.get('file_path', ''))
    if not fp:
        reps = inp.get('replacements', [])
        if reps:
            fp = reps[0].get('filePath', reps[0].get('file_path', ''))
    if fp:
        print(fp)
" 2>/dev/null || true)
}

audit_log() {
  # args: hook_name decision reason detail
  local hook_name="$1" decision="$2" reason="$3" detail="$4"
  mkdir -p "$LOG_DIR" 2>/dev/null || return 0
  python3 -c "
import json, sys, datetime as dt
entry = {
    'ts': dt.datetime.now(dt.timezone.utc).isoformat(),
    'hook': sys.argv[1],
    'tool': sys.argv[2],
    'decision': sys.argv[3],
    'reason': sys.argv[4],
    'detail': sys.argv[5][:500],
}
if sys.argv[6]:
    entry['session_id'] = sys.argv[6]
if sys.argv[7]:
    entry['tool_use_id'] = sys.argv[7]
print(json.dumps(entry))
" "$hook_name" "${TOOL_NAME:-unknown}" "$decision" "$reason" "$detail" "$SESSION_ID" "$TOOL_USE_ID" >> "$LOG_DIR/audit.jsonl" 2>/dev/null || true
}

join_file_paths() {
  if [[ ${#FILE_PATHS[@]} -eq 0 ]]; then
    echo ""
    return
  fi
  printf '%s\n' "${FILE_PATHS[@]}" | paste -sd, -
}

emit_result() {
  local message="$1"
  if [[ -z "$message" ]]; then
    echo '{}'
    return
  fi
  python3 -c "
import json, sys
print(json.dumps({'systemMessage': sys.stdin.read().strip()}))
" <<< "$(echo -e "$message")"
}
