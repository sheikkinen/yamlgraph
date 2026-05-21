# Feature Request: FR-429 Post-Edit YAML Checks

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-21

**Judge Verdict:** APPROVE — routing refactor is the real scope; this FR owns that prerequisite for FR-431.

## Summary

Extend `post-edit-checks` hook to validate YAML files (graph + prompt) immediately after agent edits, providing the same real-time feedback loop that Python files already enjoy.

## Value Statement

Agents editing graph or prompt YAML get immediate lint feedback at edit time, catching crash-causing errors (missing prompts, undefined tools, bad node types) before commit instead of at runtime.

## Problem

`post-edit-checks.sh` skips all non-`.py` files (line 61: `if [[ ! "$FILE_PATH" == *.py ]]`). Agents editing graph YAML or prompt YAML receive no feedback until `yamlgraph graph lint` is run manually or pre-commit catches issues at commit time. The linter already exists and runs in <1s, but the hook doesn't invoke it.

From audit log analysis (2026-05-20): the FR-426 enforce agent made 5+ commit attempts because issues weren't caught at edit time. YAML validation at edit time would reduce this churn.

## Proposed Solution

Branch on file extension after the existing Python check block:

### Graph YAML detection

Files are treated as graph YAML if they contain both `nodes:` and `edges:` top-level keys. This avoids false positives on CI configs, changelogs, or other YAML.

**Step 0: Routing refactor (prerequisite).** Replace the blanket `exit 0` for non-`.py` files (line 60) with file-type routing. This is the shared prerequisite for FR-431.

```bash
# Replace blanket early-exit with file-type routing
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

ISSUES=""

# ── Python file checks ──────────────────────────────────────────────
if [[ "$FILE_PATH" == *.py ]]; then
  # ... existing ruff, forbidden terms, file size, debug, noqa checks ...
fi

# ── YAML file checks ────────────────────────────────────────────────
# (graph YAML and prompt YAML blocks below)

# ── Return results ───────────────────────────────────────────────────
# ... existing JSON output block ...
```

**Step 1: Graph YAML detection.** Use `yamlgraph graph lint` exit code instead of fragile grep filtering.

```bash
if [[ "$FILE_PATH" == *.yaml || "$FILE_PATH" == *.yml ]]; then
  IS_GRAPH=$(python3 -c "
import yaml, sys
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
if isinstance(d, dict) and 'nodes' in d and 'edges' in d:
    print('graph')
" "$FILE_PATH" 2>/dev/null || true)

  if [[ "$IS_GRAPH" == "graph" ]]; then
    if command -v yamlgraph &>/dev/null; then
      LINT_OUT=$(yamlgraph graph lint "$FILE_PATH" 2>&1)
      LINT_RC=$?
      if [[ $LINT_RC -ne 0 ]] && [[ -n "$LINT_OUT" ]]; then
        ISSUES="${ISSUES}⚠ Graph lint issues:\n${LINT_OUT}\n\n"
      fi
    fi
  fi
fi
```

### Prompt YAML detection

Files under a `prompts/` directory get YAML parse validation only. Content structure validation (mixed template syntax) belongs in the linter (see FR-430).

Use `elif` to prevent double-checking a file that matches both patterns.

```bash
elif [[ "$FILE_PATH" == */prompts/*.yaml || "$FILE_PATH" == */prompts/*.yml ]]; then
  PARSE_ERR=$(python3 -c "
import yaml, sys
try:
    with open(sys.argv[1]) as f:
        yaml.safe_load(f)
except yaml.YAMLError as e:
    print(f'YAML parse error: {e}')
" "$FILE_PATH" 2>/dev/null || true)
  if [[ -n "$PARSE_ERR" ]]; then
    ISSUES="${ISSUES}⚠ Prompt file error:\n${PARSE_ERR}\n\n"
  fi
fi
```

### What this does NOT include

- No new lint rules — the hook calls existing `yamlgraph graph lint`
- No prompt content validation (mixed template syntax is FR-430, a linter feature)
- No cross-file validation beyond what the linter already does
- No changes to `pre-command-guard`

## Acceptance Criteria

- [x] Line 60 early-exit refactored to file-type routing (prerequisite for FR-431)
- [x] `post-edit-checks` runs `yamlgraph graph lint` on graph YAML files (detected by `nodes:` + `edges:` keys)
- [x] Lint result detected via exit code, not grep on output format
- [x] `post-edit-checks` runs YAML parse check on prompt YAML files (under `prompts/` dir)
- [x] Graph check and prompt check are `if`/`elif` — no double-fire
- [x] Non-graph, non-prompt YAML files are skipped (no false positives on CI YAML, changelogs, etc.)
- [x] All checks complete within the 10s hook timeout
- [x] Existing Python file checks are unchanged
- [x] Tests: bash script exercised via subprocess — graph valid/invalid, prompt valid/invalid, non-graph YAML skipped, Python file still works

## Implementation Notes (2026-05-21)

- Refactored `.github/hooks/scripts/post-edit-checks.sh` to route by file type instead of early-exiting for all non-Python edits.
- Added graph YAML detection (`nodes` + `edges`) and `yamlgraph graph lint` execution with exit-code handling.
- Added prompt YAML parse checks for files under `prompts/`.
- Extended `.github/hooks/tests/test_post_edit_checks.py` with graph/prompt YAML coverage while preserving existing Python checks.

## Alternatives Considered

- **Inline all lint checks in the hook**: Rejected — duplicates linter logic, violates `callsite_fix` (rule should live where all callers benefit).
- **Run linter on prompt files in isolation**: Not possible — linter needs a graph file as entry point. Hook covers the gap with YAML parse check only.

## Related

- [FR-430](FR-430-linter-mixed-template-syntax.md): Linter rule for mixed template syntax (W024)
- [FR-431](FR-431-fsm-reinvention-hook.md): FSM reinvention hook (depends on this FR's routing refactor)
- [post-edit-checks.sh](../.github/hooks/scripts/post-edit-checks.sh): Current implementation

## Implementation Order

This FR is the prerequisite. Order: **FR-429 → FR-430 → FR-431**.
- [graph_linter.py](../yamlgraph/linter/graph_linter.py): Linter entry point
- Diary seed (FR-425): "Can YAMLGraph detect and warn about mixed template syntax at lint time?"
- Audit log analysis (2026-05-20): 420 entries, commit thrash from late-caught errors
