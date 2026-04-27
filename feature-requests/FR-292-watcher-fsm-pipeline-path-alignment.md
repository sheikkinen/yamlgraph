# Feature Request: Watcher FSM Pipeline Config Path Alignment

**Priority:** HIGH
**Type:** Bug
**Status:** Complete
**Effort:** 0.5 days
**Requested:** 2026-04-27
**PR:** #247

## Summary
Fix 9 graph path references in `watcher-pipeline.yaml`, convert 1 action to `bash`, remove 2 states that exceed watcher2.sh parity, and simplify the pipeline to match actual production behavior.

## Value Statement
Unblocks Phase 2 (single-worker validation) by making the pipeline config point to real files — without this, every `yamlgraph_async` action fails at runtime.

## Problem
The pipeline config (`watcher-pipeline.yaml`) was written during Phase 0 with placeholder graph paths under `graphs/watcher-plan/`. The actual graphs live at `.chaplain/graphs/` under three subdirectories (`watcher-plan/`, `watcher-enforce/`, `watcher-forensic/`). Additionally:

- Some filenames don't match (e.g., `step-tests.yaml` vs actual `step-acceptance.yaml`)
- Enforcement graphs are under `watcher-enforce/`, not `watcher-plan/`
- Two referenced graphs don't exist at all (`step-split.yaml`, `step-changelog.yaml`)

## Proposed Solution

### 1. Fix graph path references in `.chaplain/config/watcher-pipeline.yaml`

| State | Current (wrong) | Correct |
|---|---|---|
| `planning` | `graphs/watcher-plan/step-plan.yaml` | `.chaplain/graphs/watcher-plan/step-plan.yaml` |
| `researching` | `graphs/watcher-plan/step-research.yaml` | `.chaplain/graphs/watcher-plan/step-research.yaml` |
| `writing_tests` | `graphs/watcher-plan/step-tests.yaml` | `.chaplain/graphs/watcher-plan/step-acceptance.yaml` |
| `judging` | `graphs/watcher-plan/step-judge.yaml` | `.chaplain/graphs/watcher-plan/step-judge.yaml` |
| `implementing` | `graphs/watcher-plan/step-implement.yaml` | `.chaplain/graphs/watcher-enforce/step-implement.yaml` |
| `testing_demo` | `graphs/watcher-plan/step-test-demo.yaml` | `.chaplain/graphs/watcher-enforce/step-test-demo.yaml` |
| `critiquing` | `graphs/watcher-plan/step-critique.yaml` | `.chaplain/graphs/watcher-enforce/step-critique.yaml` |
| `remediating_ci` | `graphs/watcher-plan/step-remediate.yaml` | `.chaplain/graphs/watcher-enforce/step-ci-remediate.yaml` |
| `forensics` | `graphs/watcher-plan/step-forensics.yaml` | `.chaplain/graphs/watcher-forensic/graph.yaml` |

### 2. Remove `splitting` state — simplify to match watcher2.sh

`watcher2.sh` treats SPLIT identical to AMEND: commit + `handle_failure` + continue. There is no dedicated split logic, no sub-topic file creation. The FSM added a `splitting` state that doesn't exist in production.

Fix: Remove `splitting` state, its action block, and the `split_done` event. Route `split` event directly to `failed` (same as `amend` already does). This removes one state, one transition, and one dead graph reference.

### 3. Remove `committing_tests` state — doesn't exist in watcher2.sh

`watcher2.sh` does NOT commit between test-demo and critique. It runs test-demo → critique → single commit ("docs: watcher2 — critique and diary"). The FSM added a `committing_tests` state + `tests_committed` event that don't correspond to any production behavior.

Fix: Remove `committing_tests` state and its action block. Route `test_demo_done` directly to `critiquing`. Remove the `tests_committed` event.

### 4. Convert `changelog_gen` action from `yamlgraph_async` to `bash`

No `step-changelog.yaml` graph exists. `watcher2.sh` generates changelog fragments via shell script, not LLM. Convert to `bash` action that:
- Reads `{fr_path}` to extract FR number and scope
- Creates `changelog/unreleased/fr-{num}-{slug}.md` with YAML front matter
- Returns `changelog_done`

### 5. Update existing tests

Update `tests/unit/test_fr291_watcher_fsm_phase1.py` to verify:
- All `yamlgraph_async` graph paths resolve to existing `.chaplain/graphs/` files
- `splitting` state removed; `split` routes to `failed`
- `committing_tests` state removed; `testing_demo` routes to `critiquing`
- `changelog_gen` uses `bash` type, not `yamlgraph_async`
- State count reduced from 27 to 25

## Acceptance Criteria
- [x] All 9 remaining `yamlgraph_async` graph paths resolve to existing `.chaplain/graphs/` files
- [x] `splitting` state removed; `split` event routes directly to `failed`
- [x] `committing_tests` state removed; `test_demo_done` routes to `critiquing`
- [x] `changelog_gen` action uses `bash` type with inline fragment generation
- [x] Pipeline reduced from 27 states to 25 states
- [x] `statemachine-validate --strict` passes on updated pipeline config
- [x] Test verifies no broken graph references (each `graph:` path exists on disk)
- [x] Tests added/updated
- [ ] Plan updated (`docs/plan-watcher-fsm.md` Phase 1.5 marked complete)

## Phase 2 Backlog (out of scope, flagged during judgement)

Functional gaps between FSM pipeline and watcher2.sh — to be addressed in Phase 2:

| Gap | Impact | Priority |
|---|---|---|
| **Dedup gate** missing | FSM will re-process already-completed FRs | HIGH |
| **`--import-state/--export-state`** not chained | Each LLM step starts without context from prior steps | HIGH |
| **CI log capture** not passed to remediation | `remediating_ci` graph can't see failure logs | MEDIUM |
| **Copilot finalize fallback** missing | Pre-commit failure after 5 retries → `failed` instead of LLM fix attempt | LOW |
| **Progressive ruff fixing** (safe → unsafe) missing | `precommit` action doesn't do `ruff check --fix --unsafe-fixes` | LOW |
| **Changelog fragment cross-validation** missing | No FR-vs-branch mismatch check | LOW |
| **Cycle metrics** (`write_cycle_metrics`) missing | `completed` state doesn't call `metrics.sh` | LOW |

## Alternatives Considered
- **Create missing graphs**: Could write `step-split.yaml` and `step-changelog.yaml` as yamlgraph graphs. Rejected — these are simple file operations, not LLM tasks. Bash is the right tool.
- **Symlink `graphs/` → `.chaplain/graphs/`**: Would fix paths without config changes. Rejected — creates invisible coupling and confuses `yamlgraph graph list`.
- **Keep `splitting` as dedicated state**: Could implement actual sub-topic creation. Rejected — watcher2.sh doesn't do this; adding functionality beyond parity is gold-plating.
- **Keep `committing_tests` state**: Could separate test-demo and critique commits. Rejected — watcher2.sh commits once after critique, not between test-demo and critique.

## Related
- FR-290: Phase 0 — original config creation
- FR-291: Phase 1 — action wiring (introduced the graph path references)
- `docs/plan-watcher-fsm.md` Phase 1.5 section
- `.chaplain/config/watcher-pipeline.yaml` (the file being fixed)
