#!/usr/bin/env bash
# PostToolUse hook: YAML checks for graph and prompt files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=.github/hooks/scripts/checks/common.sh
source "$SCRIPT_DIR/common.sh"

HOOK_NAME="post-edit-yaml-checks"
INPUT=$(cat)
parse_tool_input "$INPUT"

is_edit_tool "$TOOL_NAME" || exit 0
[[ ${#FILE_PATHS[@]} -gt 0 ]] || exit 0

build_yaml_issues() {
  local file_path="$1"
  local file_issues=""

  [[ -f "$file_path" ]] || return 0
  if [[ ! "$file_path" == *.yaml && ! "$file_path" == *.yml ]]; then
    return 0
  fi

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

  if [[ -n "$file_issues" ]]; then
    printf 'File: %s\n%s' "$file_path" "$file_issues"
  fi
}

ALL_ISSUES=""
for target_file in "${FILE_PATHS[@]}"; do
  [[ -n "$target_file" ]] || continue
  FILE_ISSUES=$(build_yaml_issues "$target_file")
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
