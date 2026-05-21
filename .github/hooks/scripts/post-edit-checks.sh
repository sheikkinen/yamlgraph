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
  replace_string_in_file|create_file|multi_replace_string_in_file|apply_patch) ;;
  *) exit 0 ;;
esac

# ── Extract file paths ───────────────────────────────────────────────
FILE_PATHS=$(echo "$INPUT" | python3 -c "
import sys, json
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

# Skip if no touched files were detected
if [[ -z "$FILE_PATHS" ]]; then
  exit 0
fi

build_file_issues() {
  local file_path="$1"
  local file_issues=""

  # Skip if file doesn't exist
  if [[ ! -f "$file_path" ]]; then
    echo ""
    return
  fi

  # ── Python file checks ─────────────────────────────────────────────
  if [[ "$file_path" == *.py ]]; then
    # Optional Phase 2 auto-fix (default off)
    if [[ "${POST_EDIT_AUTO_RUFF:-}" == "1" ]] && command -v ruff &>/dev/null; then
      local before_sig
      local after_sig
      before_sig=$(cksum "$file_path" | awk '{print $1":"$2}')
      ruff check --fix --quiet "$file_path" >/dev/null 2>&1 || true
      ruff format --quiet "$file_path" >/dev/null 2>&1 || true
      after_sig=$(cksum "$file_path" | awk '{print $1":"$2}')
      if [[ "$before_sig" != "$after_sig" ]]; then
        audit_log "feedback" "ruff-autofix-applied" "$file_path"
      fi
    fi

    # 1. Ruff lint
    if command -v ruff &>/dev/null; then
      local ruff_lint
      ruff_lint=$(ruff check --no-fix --quiet "$file_path" 2>/dev/null || true)
      if [[ -n "$ruff_lint" ]]; then
        file_issues="${file_issues}⚠ Ruff lint errors:\n${ruff_lint}\n\n"
      fi
    else
      audit_log "error" "ruff-missing" "$file_path"
    fi

    # 2. Ruff format check
    if command -v ruff &>/dev/null; then
      local ruff_fmt
      ruff_fmt=$(ruff format --check --quiet "$file_path" 2>&1 || true)
      if echo "$ruff_fmt" | grep -q "would reformat\|reformatted"; then
        file_issues="${file_issues}⚠ Ruff format: file needs reformatting. Run: ruff format ${file_path}\n\n"
      fi
    fi

    # 3. Forbidden terms (TODO, FIXME, backward compatibility)
    local forbidden
    forbidden=$(grep -nE 'TODO|FIXME|backward compati(bility)?' "$file_path" 2>/dev/null || true)
    if [[ -n "$forbidden" ]]; then
      file_issues="${file_issues}⚠ Forbidden terms found (pre-commit will reject):\n${forbidden}\n\n"
    fi

    # 4. File size
    local line_count
    line_count=$(wc -l < "$file_path" | tr -d ' ')
    if [[ "$line_count" -gt 450 ]]; then
      file_issues="${file_issues}✗ File size: ${line_count} lines (max 450). Split into submodules.\n\n"
    elif [[ "$line_count" -gt 400 ]]; then
      file_issues="${file_issues}⚠ File size: ${line_count} lines (target ≤400). Consider splitting.\n\n"
    fi

    # 5. Debug statements
    local debug
    debug=$(grep -nE '^\s*(import pdb|from pdb import|breakpoint\(\))' "$file_path" 2>/dev/null || true)
    if [[ -n "$debug" ]]; then
      file_issues="${file_issues}⚠ Debug statements found (pre-commit will reject):\n${debug}\n\n"
    fi

    # 6. noqa without confession (cross-reference docs/confessions.md)
    local noqa_lines
    noqa_lines=$(grep -nE '#\s*noqa' "$file_path" 2>/dev/null || true)
    if [[ -n "$noqa_lines" ]]; then
      local proj_root
      local confessions
      local rel_path
      proj_root=$(cd "$(dirname "$file_path")" && git rev-parse --show-toplevel 2>/dev/null || echo "")
      confessions="${proj_root}/docs/confessions.md"
      rel_path=""
      if [[ -n "$proj_root" ]]; then
        rel_path="${file_path#$proj_root/}"
      fi

      local undocumented
      undocumented=""
      while IFS= read -r line; do
        local lineno_num
        lineno_num=$(echo "$line" | cut -d: -f1)
        if [[ -f "$confessions" ]] && [[ -n "$rel_path" ]]; then
          if grep -q "${rel_path}#L${lineno_num}" "$confessions" 2>/dev/null; then
            continue
          fi
        fi
        undocumented="${undocumented}  ${line}\n"
      done <<< "$noqa_lines"

      if [[ -n "$undocumented" ]]; then
        file_issues="${file_issues}⚠ noqa without confession in docs/confessions.md (pre-commit will reject):\n${undocumented}Add CONF-XXX entry with File, Code, Sin, and Penance.\n\n"
      fi
    fi
  fi

  # ── YAML file checks ───────────────────────────────────────────────
  if [[ "$file_path" == *.yaml || "$file_path" == *.yml ]]; then
    local is_graph
    is_graph=$(python3 -c "
import sys
import yaml

with open(sys.argv[1], encoding='utf-8') as f:
    data = yaml.safe_load(f)

if isinstance(data, dict) and 'nodes' in data and 'edges' in data:
    print('graph')
" "$file_path" 2>/dev/null || true)

    if [[ "$is_graph" == "graph" ]]; then
      if command -v yamlgraph &>/dev/null; then
        local lint_out
        local lint_rc
        if lint_out=$(yamlgraph graph lint "$file_path" 2>&1); then
          lint_rc=0
        else
          lint_rc=$?
        fi
        if [[ $lint_rc -ne 0 ]] && [[ -n "$lint_out" ]]; then
          file_issues="${file_issues}⚠ Graph lint issues:\n${lint_out}\n\n"
        fi
      fi
    elif [[ "$file_path" == */prompts/*.yaml || "$file_path" == */prompts/*.yml ]]; then
      local parse_err
      parse_err=$(python3 -c "
import sys
import yaml

try:
    with open(sys.argv[1], encoding='utf-8') as f:
        yaml.safe_load(f)
except yaml.YAMLError as exc:
    print(f'YAML parse error: {exc}')
" "$file_path" 2>/dev/null || true)
      if [[ -n "$parse_err" ]]; then
        file_issues="${file_issues}⚠ Prompt file error:\n${parse_err}\n\n"
      fi
    fi
  fi

  # ── Feature request checks ─────────────────────────────────────────
  if [[ "$file_path" == */feature-requests/*.md ]]; then
    local fsm_hit
    fsm_hit=$(python3 -c "
import re
import sys

text = open(sys.argv[1], encoding='utf-8').read().lower()

escapes = [
    'statemachine_engine',
    'statemachine-engine',
    'fsm-as-conductor',
    'yamlgraph.utils.fsm',
    'yamlgraph/utils/fsm',
]
if any(e in text for e in escapes):
    sys.exit(0)

signals = [
    r'\\bstate\\s*machine\\b',
    r'\\bfinite\\s*state\\b',
    r'\\bfsm\\b',
    r'\\bstates\\s+and\\s+transitions\\b',
    r'\\bstate\\s*diagram\\b',
    r'\\blifecycle\\s+management\\b',
    r'\\bworkflow\\s+states?\\b',
    r'\\bpolling\\s+loop\\b',
    r'\\bevent[- ]driven\\s+workflow\\b',
    r'\\bevent\\s+dispatch\\b',
    r'\\bguard\\s+condition\\b',
    r'\\bstate\\s+transition\\b',
    r'\\btransition\\s+guard\\b',
]
hits = sum(1 for pattern in signals if re.search(pattern, text))
if hits >= 2:
    print('fsm_reinvention')
" "$file_path" 2>/dev/null || true)

    if [[ "$fsm_hit" == "fsm_reinvention" ]]; then
      file_issues="${file_issues}⚠ FSM patterns detected - see reference/patterns/fsm-as-conductor.md before reinventing.\n\n"
    fi
  fi

  echo "$file_issues"
}

ALL_ISSUES=""
while IFS= read -r target_file; do
  if [[ -z "$target_file" ]]; then
    continue
  fi
  FILE_ISSUES=$(build_file_issues "$target_file")
  if [[ -n "$FILE_ISSUES" ]]; then
    ALL_ISSUES="${ALL_ISSUES}File: ${target_file}\n${FILE_ISSUES}"
  fi
done <<< "$FILE_PATHS"

# ── Return results ───────────────────────────────────────────────────
if [[ -z "$ALL_ISSUES" ]]; then
  audit_log "approve" "all-checks-clean" "$(echo "$FILE_PATHS" | paste -sd, -)"
  echo '{}'
  exit 0
fi

audit_log "feedback" "issues-found" "$(echo "$FILE_PATHS" | paste -sd, -)"

# Build JSON with systemMessage using python for safe escaping
python3 -c "
import json, sys
msg = sys.stdin.read().strip()
print(json.dumps({'systemMessage': msg}))
" <<< "$(echo -e "$ALL_ISSUES")"

exit 0
