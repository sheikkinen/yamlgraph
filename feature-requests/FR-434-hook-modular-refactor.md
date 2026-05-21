# Feature Request: FR-434 Hook Scripts Modular Refactor

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-05-21

## Summary

Split the `post-edit-checks.sh` monolith (243 lines, growing) into separate hook scripts per concern, using the VS Code hook JSON config as the dispatcher instead of bash routing.

## Value Statement

Hook maintainers can add new check types by adding a JSON entry + a focused script, without touching existing scripts or a shared dispatcher.

## Problem

`post-edit-checks.sh` is a single monolith handling Python checks, YAML checks, FR markdown checks, input parsing, audit logging, and JSON output. With FR-433 adding `apply_patch` multi-file support, it will grow past 300 lines. The test file is already 619 lines.

Scripture: Commandment 8 — "Split modules before they bloat."

## Proposed Solution

### Architecture: JSON config as dispatcher

VS Code supports **multiple hook entries per event** in the JSON array — it runs all of them. Instead of a bash dispatcher routing file types, register each check as a separate PostToolUse hook. VS Code itself becomes the dispatcher.

**Key constraint:** VS Code parses but **ignores** matchers — all hooks fire on every tool invocation regardless of tool name. Each script must filter irrelevant invocations internally via early exit.

**Key assumption:** When multiple PostToolUse hooks emit `systemMessage` (e.g., `apply_patch` touching both `.py` and `.yaml` files), VS Code's aggregation behavior is undocumented. If only the last message survives, use `hookSpecificOutput.additionalContext` instead. Verify before implementing.

### Hook JSON config

Replace single `post-edit-checks.json` with `post-edit-checks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": ".github/hooks/scripts/checks/python-checks.sh",
        "timeout": 10
      },
      {
        "type": "command",
        "command": ".github/hooks/scripts/checks/yaml-checks.sh",
        "timeout": 10
      },
      {
        "type": "command",
        "command": ".github/hooks/scripts/checks/fr-checks.sh",
        "timeout": 5
      }
    ]
  }
}
```

### Directory structure

```
.github/hooks/
├── scripts/
│   ├── checks/                       # Per-concern check scripts
│   │   ├── common.sh                 # audit_log(), parse_tool_input(), emit_result()
│   │   ├── python-checks.sh          # ruff, forbidden terms, file size, debug, noqa
│   │   ├── yaml-checks.sh            # graph lint, prompt parse
│   │   └── fr-checks.sh              # FSM reinvention, future FR checks
│   ├── pre-command-guard.sh          # Unchanged (185 lines, within budget)
│   ├── classify-emit.sh              # Unchanged (47 lines)
│   └── session-timeline.py           # Unchanged
├── tests/
│   ├── test_python_checks.py         # Python check tests
│   ├── test_yaml_checks.py           # YAML check tests
│   ├── test_fr_checks.py             # FR check tests
│   ├── test_pre_command_guard.py     # Unchanged
│   └── test_session_timeline.py      # Unchanged
├── post-edit-checks.json             # Multiple PostToolUse entries
├── pre-command-guard.json            # Unchanged
└── classify-emit.json                # Unchanged
```

### Check script contract

Each script in `checks/` follows the same pattern:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/common.sh"

INPUT=$(cat)
parse_tool_input "$INPUT"

# ── Relevance filter (early exit) ───────────────────────────────────
is_edit_tool "$TOOL_NAME" || exit 0
[[ "$FILE_PATH" == *.py ]] || exit 0   # or *.yaml, */feature-requests/*.md
[[ -f "$FILE_PATH" ]] || exit 0

# ── Checks ──────────────────────────────────────────────────────────
ISSUES=""
# ... file-type-specific checks ...

# ── Output ──────────────────────────────────────────────────────────
emit_result "$ISSUES"
```

### `common.sh` shared helpers (~40 lines)

```bash
# Shared edit-tool names
is_edit_tool() {
  case "$1" in
    replace_string_in_file|create_file|multi_replace_string_in_file|apply_patch) return 0 ;;
    *) return 1 ;;
  esac
}

# Parse tool input JSON → TOOL_NAME, SESSION_ID, FILE_PATH, FILE_PATHS[]
# For apply_patch: FILE_PATHS[] populated with all affected paths
# Single-file tools: FILE_PATHS=("$FILE_PATH")
parse_tool_input() { ... }

# Iterate FILE_PATHS, yield only those matching a glob
# Usage: for_matching_files "*.py" run_python_check
for_matching_files() { ... }

# Audit log to JSONL
audit_log() { ... }

# Emit JSON result or empty {}
emit_result() { ... }
```

### Tradeoffs vs bash dispatcher

| | JSON dispatcher | Bash dispatcher |
|---|---|---|
| **Adding a check type** | Add JSON entry + script | Edit dispatcher + add script |
| **Process overhead** | 3 process spawns per tool use | 1 process spawn |
| **Tool-name filtering** | Duplicated in each script (via `common.sh`) | Once in dispatcher |
| **Independence** | Each script is fully standalone | Scripts share process state |
| **Testability** | Each script testable in isolation | Need to test routing + checks |
| **Timeout** | Per-script (can give Python 10s, FR 5s) | Shared 10s for all |
| **Failure isolation** | One script failing doesn't block others | One failure can cascade |

The **per-script timeout** is a significant advantage — Python checks (ruff) need more time than FR keyword matching. The **failure isolation** means a broken YAML check doesn't prevent Python checks from running.

The 3-process overhead is negligible — each script exits in <100ms when the file type doesn't match (`exit 0` after `is_edit_tool` + extension check).

### What this does NOT change

- pre-command-guard.sh — 185 lines, within budget, no split needed
- classify-emit.sh — 47 lines, trivial
- Hook behavior — all checks identical, just reorganized

## Acceptance Criteria

- [ ] `post-edit-checks.json` contains multiple PostToolUse entries (one per check script)
- [ ] `checks/python-checks.sh` contains all Python file checks (ruff, forbidden terms, file size, debug, noqa)
- [ ] `checks/yaml-checks.sh` contains graph lint + prompt parse checks
- [ ] `checks/fr-checks.sh` contains FR markdown checks (FSM reinvention)
- [ ] `checks/common.sh` contains shared helpers (audit_log, parse_tool_input, is_edit_tool, emit_result)
- [ ] Each check script filters irrelevant invocations and exits cleanly
- [ ] Per-script timeouts: Python 10s, YAML 10s, FR 5s
- [ ] All existing check behaviors preserved (behavioral equivalence)
- [ ] Each check script independently testable
- [ ] Old `post-edit-checks.sh` deleted
- [ ] `grep -r 'post-edit-checks.sh'` confirms zero references after migration
- [ ] Verify VS Code systemMessage aggregation when multiple hooks emit for same tool invocation
- [ ] Test migration: existing test functions mapped to new files, shared fixtures in `conftest.py`

## Implementation Order

After FR-433 (apply_patch coverage) to avoid refactoring twice.

Order: FR-429 → FR-433 → **FR-434** → future checks add a JSON entry + script without touching existing files.

## Alternatives Considered

- **Bash dispatcher (original FR-434 plan)**: Single process, internal routing via `case`. Simpler but still a growing monolith — the dispatcher itself becomes the new bottleneck. Doesn't leverage VS Code's native multi-hook support.
- **Rewrite hooks in Python**: More testable, but VS Code hook contract expects shell commands with stdout JSON. Python needs a bash wrapper anyway.
- **One function per check in the same file**: Reduces monolith feel but doesn't solve file-size growth or independent testability.
- **Move checks to yamlgraph CLI**: Wrong boundary — hooks are editor infrastructure, not framework features.

## Related

- [VS Code hooks docs](https://code.visualstudio.com/docs/copilot/customization/hooks): Multiple PostToolUse entries supported; matchers ignored
- [post-edit-checks.sh](../.github/hooks/scripts/post-edit-checks.sh): Current 243-line monolith
- [FR-429](FR-429-post-edit-yaml-checks.md): YAML checks
- [FR-431](FR-431-fsm-reinvention-hook.md): FR checks
- [FR-433](FR-433-post-edit-apply-patch-coverage-and-auto-ruff.md): apply_patch + multi-file
