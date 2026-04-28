# Feature Request: Watcher-FSM Phase 2 — Single-Worker Validation

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-04-28

## Summary

Run the FSM pipeline end-to-end on a real topic. One topic in, one merged PR out. watcher2.sh remains the production fallback; the FSM uses a separate test inbox.

## Value Statement

Proves the declarative FSM pipeline produces the same outcome as the 524-line bash script — the gate to retirement.

## Problem

Phases 0–1.5 delivered validated configs, wired actions, and aligned paths — but the FSM has never processed a real topic. Without an end-to-end run, the configs are untested theory.

## Proposed Solution

### 1. Test Inbox Setup

Create `.chaplain/inbox-fsm/` as an isolated test inbox. The dispatcher reads from this directory instead of production `.chaplain/inbox/`. Both systems coexist without conflict.

### 2. Dispatcher Integration

The dispatcher (`watcher-dispatcher.yaml`) already spawns the pipeline via:

```yaml
processing_topic:
  - type: bash
    command: >-
      statemachine .chaplain/config/watcher-pipeline.yaml
      --actions-dir .chaplain/actions
      --context topic_file={topic_file}
```

Phase 2 validates this works end-to-end, not just in unit tests.

### 3. Validation Script

`.chaplain/scripts/validate-fsm-single.sh` — runs the dispatcher in single-cycle mode (process one topic, then stop). Asserts:
- All expected states visited in order (preflight → ... → cleaning_up → completed)
- PR created and merged on GitHub
- Worktree cleaned up (no stale dirs)
- No errors in logs

### 4. Test Scenarios

Run manually, one at a time:

| # | Scenario | Expected path |
|---|----------|--------------|
| 1 | Happy path (trivial docs fix) | preflight → ... → merging → cleaning_up → completed |
| 2 | Reject (bad topic) | judging → failed → forensics → completed |
| 3 | Preflight failure (not on main) | preflight → failed → forensics → completed |
| 4 | Pre-commit retry | finalizing → precommit_retry → finalizing → ... → completed |

## Acceptance Criteria

- [ ] `.chaplain/inbox-fsm/` directory exists (gitignored)
- [ ] Dispatcher reads from configurable inbox dir (via `--context inbox_dir=...`)
- [ ] Validation script processes one topic end-to-end
- [ ] Happy path: topic → PR merged → worktree cleaned
- [ ] Failure path: bad topic → failed → forensics → completed
- [ ] watcher2.sh still works on production inbox (coexistence verified)
- [ ] Tests added
- [ ] Diary reflection

## Alternatives Considered

- **Run on production inbox**: Too risky — if FSM breaks mid-pipeline, production topics could be left in limbo. Separate inbox eliminates this.
- **Mock LLM calls**: Defeats the purpose — we need to validate the full stack including real LLM responses, real git operations, real CI.

## Related

- FR-290: Phase 0 — configs (PR #245)
- FR-291: Phase 1 — action wiring (PR #246)
- FR-292: Phase 1.5 — path alignment (PR #247)
- Plan: `docs/plan-watcher-fsm.md` (Phase 2 section)
- Dispatcher: `.chaplain/config/watcher-dispatcher.yaml`
- Pipeline: `.chaplain/config/watcher-pipeline.yaml`
- Actions: `.chaplain/actions/`

## Implementation Notes

### What needs to change

1. **Dispatcher config** — make inbox path configurable (currently hardcoded to `.chaplain/inbox/`)
2. **Validation script** — new `.chaplain/scripts/validate-fsm-single.sh`
3. **Test topic** — trivial docs-only change that will pass judge + CI
4. **`.gitignore`** — add `.chaplain/inbox-fsm/`

### What stays unchanged

- Pipeline config (already aligned in FR-292)
- All 4 action scripts (already tested in FR-291)
- All lib scripts (already augmented with JSON stdout)
- watcher2.sh (production fallback, untouched)

### Risk: LLM non-determinism

The judge may reject a topic we expect to pass. Mitigation: use a maximally trivial topic (typo fix in docs) and accept that the first run may need one retry with a better-crafted topic.

### Risk: statemachine-engine CLI gaps

The FSM engine has been tested via Python API in unit tests but never via CLI with real actions. Gaps may surface in:
- Context passing between states
- Event extraction from action output
- Timeout handling
- Error → failed transition wiring

These are the bugs we want to find.
