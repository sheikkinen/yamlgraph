#!/usr/bin/env bash
# PostToolUse hook: Python checks for edited files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=.github/hooks/scripts/checks/common.sh
source "$SCRIPT_DIR/common.sh"

HOOK_NAME="post-edit-python-checks"
INPUT=$(cat)
parse_tool_input "$INPUT"

is_edit_tool "$TOOL_NAME" || exit 0
[[ ${#FILE_PATHS[@]} -gt 0 ]] || exit 0

RUFF_BIN=$(resolve_ruff || true)

build_python_issues() {
  local file_path="$1"
  local file_issues=""

  [[ -f "$file_path" ]] || return 0
  [[ "$file_path" == *.py ]] || return 0

  if [[ -n "$RUFF_BIN" ]]; then
    if [[ "${POST_EDIT_AUTO_RUFF:-}" == "1" ]]; then
      local before_sig
      local after_sig
      before_sig=$(cksum "$file_path" | awk '{print $1":"$2}')
      "$RUFF_BIN" check --fix --quiet "$file_path" >/dev/null 2>&1 || true
      "$RUFF_BIN" format --quiet "$file_path" >/dev/null 2>&1 || true
      after_sig=$(cksum "$file_path" | awk '{print $1":"$2}')
      if [[ "$before_sig" != "$after_sig" ]]; then
        audit_log "$HOOK_NAME" "feedback" "ruff-autofix-applied" "$file_path"
      fi
    fi

    local ruff_lint
    ruff_lint=$("$RUFF_BIN" check --no-fix --quiet "$file_path" 2>/dev/null || true)
    if [[ -n "$ruff_lint" ]]; then
      file_issues="${file_issues}⚠ Ruff lint errors:\n${ruff_lint}\n\n"
    fi

    local ruff_fmt
    ruff_fmt=$("$RUFF_BIN" format --check --quiet "$file_path" 2>&1 || true)
    if echo "$ruff_fmt" | grep -q "would reformat\|reformatted"; then
      file_issues="${file_issues}⚠ Ruff format: file needs reformatting. Run: ruff format ${file_path}\n\n"
    fi
  else
    audit_log "$HOOK_NAME" "error" "ruff-missing" "$file_path"
  fi

  local forbidden
  forbidden=$(grep -nE 'TODO|FIXME|backward compati(bility)?' "$file_path" 2>/dev/null || true)
  if [[ -n "$forbidden" ]]; then
    file_issues="${file_issues}⚠ Forbidden terms found (pre-commit will reject):\n${forbidden}\n\n"
  fi

  local line_count
  line_count=$(wc -l < "$file_path" | tr -d ' ')
  if [[ "$line_count" -gt 450 ]]; then
    file_issues="${file_issues}✗ File size: ${line_count} lines (max 450). Split into submodules.\n\n"
  elif [[ "$line_count" -gt 400 ]]; then
    file_issues="${file_issues}⚠ File size: ${line_count} lines (target ≤400). Consider splitting.\n\n"
  fi

  local debug
  debug=$(grep -nE '^\s*(import pdb|from pdb import|breakpoint\(\))' "$file_path" 2>/dev/null || true)
  if [[ -n "$debug" ]]; then
    file_issues="${file_issues}⚠ Debug statements found (pre-commit will reject):\n${debug}\n\n"
  fi

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

  if [[ -n "$file_issues" ]]; then
    printf 'File: %s\n%s' "$file_path" "$file_issues"
  fi
}

ALL_ISSUES=""
for target_file in "${FILE_PATHS[@]}"; do
  [[ -n "$target_file" ]] || continue
  FILE_ISSUES=$(build_python_issues "$target_file")
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
