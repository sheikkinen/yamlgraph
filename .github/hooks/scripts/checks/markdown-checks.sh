#!/usr/bin/env bash
# PostToolUse hook: markdown hygiene checks.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=.github/hooks/scripts/checks/common.sh
source "$SCRIPT_DIR/common.sh"

HOOK_NAME="post-edit-markdown-checks"
INPUT=$(cat)
parse_tool_input "$INPUT"

is_edit_tool "$TOOL_NAME" || exit 0
[[ ${#FILE_PATHS[@]} -gt 0 ]] || exit 0

build_markdown_issues() {
  local file_path="$1"
  local file_issues=""

  [[ -f "$file_path" ]] || return 0
  [[ "$file_path" == *.md ]] || return 0
  [[ ! "$file_path" == */feature-requests/*.md ]] || return 0

  if [[ "${POST_EDIT_AUTO_MD:-}" == "1" ]]; then
    local before_sig
    local after_sig
    before_sig=$(cksum "$file_path" | awk '{print $1":"$2}')

    python3 -c "
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
trimmed = []
for line in lines:
    if line.endswith('\n'):
        body = line[:-1].rstrip(' \t')
        trimmed.append(body + '\n')
    else:
        trimmed.append(line.rstrip(' \t'))
path.write_text(''.join(trimmed), encoding='utf-8')
" "$file_path"

    after_sig=$(cksum "$file_path" | awk '{print $1":"$2}')
    if [[ "$before_sig" != "$after_sig" ]]; then
      audit_log "$HOOK_NAME" "feedback" "markdown-autofix-applied" "$file_path"
    fi
  fi

  local trailing
  trailing=$(grep -nE '[[:blank:]]+$' "$file_path" 2>/dev/null || true)
  if [[ -n "$trailing" ]]; then
    file_issues="${file_issues}⚠ Markdown trailing whitespace found:\n${trailing}\n\n"
  fi

  if [[ -n "$file_issues" ]]; then
    printf 'File: %s\n%s' "$file_path" "$file_issues"
  fi
}

ALL_ISSUES=""
for target_file in "${FILE_PATHS[@]}"; do
  [[ -n "$target_file" ]] || continue
  FILE_ISSUES=$(build_markdown_issues "$target_file")
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
