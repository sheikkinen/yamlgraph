# Feature Request: FR-431 FSM Reinvention Detection Hook

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-05-21

**Judge Verdict:** APPROVE — drop `retry.*backoff` (not FSM-specific), tighten `event-driven` to `event-driven workflow`, add FR-429 dependency.

## Summary

Add a post-edit hook check that warns when a feature request describes FSM/state-machine patterns without referencing `statemachine_engine` — the project's existing FSM integration.

## Value Statement

Agents get a just-in-time pointer to the existing FSM bridge when they're about to reinvent it, without bloating the system prompt context on every interaction.

## Problem

`copilot-instructions.md` and `CLAUDE.md` have zero mentions of `statemachine_engine`, the FSM bridge in `yamlgraph/utils/fsm/`, or the `fsm-as-conductor` pattern. Agents writing feature requests can propose building state management, lifecycle orchestration, retry loops, or event dispatch systems in pure Python — unaware that a mature, tested bridge already exists with three production instances.

Adding this knowledge to the system prompt would waste context on every interaction. A hook delivers the information only when relevant: at the moment an FR is being written that exhibits FSM-reinvention signals.

Scripture trap: `continuation_bias` — "Default mode is text generation → search before implementing." The agent can't search for what it doesn't know exists.

## Proposed Solution

Extend `post-edit-checks.sh` to handle `feature-requests/*.md` files with a keyword-based FSM reinvention detector.

### Detection logic

```bash
# ── FR FSM-reinvention check ────────────────────────────────────────
# Trigger: file matches */feature-requests/*.md
# Signal: 2+ FSM keywords present without escape-hatch references
# Output: warning with pointer to existing integration

if [[ "$FILE_PATH" == */feature-requests/*.md ]] && [[ -f "$FILE_PATH" ]]; then
  FSM_HIT=$(python3 -c "
import re, sys

text = open(sys.argv[1]).read().lower()

# Escape hatches: FR already references the existing FSM integration
escapes = ['statemachine_engine', 'statemachine-engine',
           'fsm-as-conductor', 'yamlgraph.utils.fsm',
           'yamlgraph/utils/fsm']
for e in escapes:
    if e in text:
        sys.exit(0)

# Signal keywords (need 2+ hits to flag)
signals = [
    r'\bstate\s*machine\b', r'\bfinite\s*state\b', r'\bfsm\b',
    r'\bstates\s+and\s+transitions\b', r'\bstate\s*diagram\b',
    r'\blifecycle\s+management\b', r'\bworkflow\s+states?\b',
    r'\bpolling\s+loop\b', r'\bevent[- ]driven\s+workflow\b',
    r'\bevent\s+dispatch\b', r'\bguard\s+condition\b',
    r'\bstate\s+transition\b', r'\btransition\s+guard\b',
]
hits = sum(1 for s in signals if re.search(s, text))
if hits >= 2:
    print('fsm_reinvention')
" "$FILE_PATH" 2>/dev/null || true)

  if [[ "$FSM_HIT" == "fsm_reinvention" ]]; then
    ISSUES="${ISSUES}⚠ FSM patterns detected — see reference/patterns/fsm-as-conductor.md before reinventing.\n\n"
  fi
fi
```

### Hook changes required

**Depends on FR-429** which refactors the line-60 early-exit into file-type routing. This FR adds the `feature-requests/*.md` block to that routing structure.

```bash
# Replace the blanket early-exit with file-type routing
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

ISSUES=""

# ── Python file checks ──────────────────────────────────────────────
if [[ "$FILE_PATH" == *.py ]]; then
  # ... existing ruff, forbidden terms, file size, debug, noqa checks ...
fi

# ── Feature request checks ──────────────────────────────────────────
if [[ "$FILE_PATH" == */feature-requests/*.md ]]; then
  # ... FSM reinvention check ...
fi

# ── Return results ───────────────────────────────────────────────────
# ... existing JSON output block ...
```

### What this does NOT include

- No changes to copilot-instructions.md or CLAUDE.md (hook delivers awareness at point of need)
- No denial — warning only; agent proceeds if the FR legitimately needs new FSM logic
- No semantic/LLM-based analysis — pure keyword matching, fast and deterministic

## Acceptance Criteria

- [ ] `post-edit-checks` fires on `feature-requests/*.md` file edits (routing from FR-429)
- [ ] Warning emitted when 2+ FSM signal keywords found without escape-hatch references
- [ ] No false positive when FR mentions `statemachine_engine`, `statemachine-engine`, `fsm-as-conductor`, or `yamlgraph.utils.fsm`
- [ ] No false positive on non-FR markdown files (changelogs, docs, diary)
- [ ] Existing Python checks unaffected
- [ ] All checks complete within 10s hook timeout
- [ ] Tests: FR with FSM signals → warning, FR with escape hatch → clean, FR without signals → clean

## Dependencies

- **FR-429**: Routing refactor (line-60 early-exit → file-type dispatch)

## Alternatives Considered

- **Add statemachine_engine to copilot-instructions.md**: Wastes context on every interaction. Hook delivers info only when relevant.
- **Add to Chaplain judge step**: Judge already runs semantic analysis; could classify against capabilities inventory. But that's a heavier solution for a keyword-level problem. Could be a future evolution (see Seed in prior reflection).
- **Pre-command guard**: Operates on terminal commands, not file content. Wrong hook type.

## Related

- [reference/patterns/fsm-as-conductor.md](../reference/patterns/fsm-as-conductor.md): The pattern doc the warning points to
- [yamlgraph/utils/fsm/](../yamlgraph/utils/fsm/): The bridge module agents should know about
- [FR-429](FR-429-post-edit-yaml-checks.md): Post-edit YAML checks (same hook, different file type)
- [FR-425](FR-425-hook-classification-daemon.md): Hook classification daemon (originated the hook reflection)
- [post-edit-checks.sh](../.github/hooks/scripts/post-edit-checks.sh): Current implementation
