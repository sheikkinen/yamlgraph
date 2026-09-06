#!/usr/bin/env bash
# PostToolUse hook: feature request markdown checks.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=.github/hooks/scripts/checks/common.sh
source "$SCRIPT_DIR/common.sh"

HOOK_NAME="post-edit-fr-checks"
INPUT=$(cat)
parse_tool_input "$INPUT"

is_edit_tool "$TOOL_NAME" || exit 0
[[ ${#FILE_PATHS[@]} -gt 0 ]] || exit 0

build_fr_issues() {
  local file_path="$1"
  local file_issues=""

  [[ -f "$file_path" ]] || return 0
  [[ "$file_path" == */feature-requests/*.md ]] || return 0

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

  # FR-737: prior-art retrieval on NEWLY CREATED FRs only — tracked files
  # (status edits, judgement folds) never re-nag.
  local is_tracked=0
  if git -C "$(dirname "$file_path")" ls-files --error-unmatch "$(basename "$file_path")" >/dev/null 2>&1; then
    is_tracked=1
  fi
  if [[ "$is_tracked" -eq 0 ]]; then
    local prior_art
    prior_art=$(python3 "$SCRIPT_DIR/prior_art.py" "$file_path" 2>/dev/null || true)
    if [[ -n "$prior_art" ]]; then
      file_issues="${file_issues}${prior_art}\n"
    fi
    # FR-745 F1: reminder only — no LLM at hook time. Run the triage graph
    # before judgement: yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=<fr>
    file_issues="${file_issues}ℹ FR-745: run fr_triage before judgement (canon answers + pre-mortem witnesses become dispositionable claims).\n\n"
  fi

  if [[ -n "$file_issues" ]]; then
    printf 'File: %s\n%s' "$file_path" "$file_issues"
  fi
}

ALL_ISSUES=""
for target_file in "${FILE_PATHS[@]}"; do
  [[ -n "$target_file" ]] || continue
  FILE_ISSUES=$(build_fr_issues "$target_file")
  if [[ -n "$FILE_ISSUES" ]]; then
    ALL_ISSUES="${ALL_ISSUES}${FILE_ISSUES}"
  fi
done

if [[ -z "$ALL_ISSUES" ]]; then
  audit_log "$HOOK_NAME" "approve" "all-checks-clean" "$(join_file_paths)"
  emit_result ""
  exit 0
fi

audit_log "$HOOK_NAME" "feedback" "issues-found" "$(join_file_paths)"
emit_result "$ALL_ISSUES"
exit 0
