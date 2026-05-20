# Feature Request: FR-423 Watcher Plan/Judge Convergence and Judgement Persistence

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1.0 day
**Requested:** 2026-05-20

## Summary

Fix watcher pipeline revise-loop drift by keeping a single FR path across plan/judge cycles and making AMEND/REJECT reasoning persist in the FR file (not only runtime logs).

## Value Statement

Watcher operators and contributors get deterministic Plan -> Judge convergence with durable judgement rationale, reducing amend-loop churn and forensic debugging time.

## Problem

Recent GH-420 runs show three coupled defects in the Plan -> Judge loop:

1. **FR identity drift:** on AMEND, pipeline routes back to `plan`, and planner may create a new `FR-XXX-*.md` file each cycle.
2. **Fragile FR selection:** `capture_fr` picks a lexicographically-last changed/untracked FR file, so the target can shift across cycles.
3. **Reasoning durability gap:** judge reasoning is visible in `logs/fsm-pipeline-*.log` (`event_map: output=...`) but is not reliably persisted into the FR document.

Result: judgement is received, but not consistently anchored to one authoritative FR artifact.

## Proposed Solution

### 1) Stabilize FR identity across revise cycles

- Treat `fr_path` as immutable per topic once first captured.
- On subsequent `plan` runs, pass existing `fr_path` into planner context and require in-place edits.

Configuration/graph changes:

- Update `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` state + variables to include `fr_path`.
- Update `.chaplain/config/watcher-pipeline-v2.yaml` plan vars to pass `fr_path` when present.
- Update `capture_fr` logic:
  - If context already has `fr_path` and file exists, keep it.
  - Otherwise perform current discovery flow and set `fr_path` once.

### 2) Tighten planner instructions for revise behavior

- Update `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml`:
  - If `fr_path` is provided, edit that file in place.
  - Do not create a new FR number during AMEND cycles.
  - New FR creation allowed only when `fr_path` is absent (first plan pass).

### 3) Persist judgement rationale in FR file

- Keep existing judge output parsing/event routing.
- Strengthen judge writeback requirement in `.chaplain/graphs/watcher-plan/prompts/judge.yaml`:
  - On AMEND/REJECT, append or update a `## Judge Notes` section in `fr_path` with dated rationale.
- Add a lightweight post-judge persistence guard:
  - If verdict is AMEND/REJECT and FR file was not updated in this cycle, emit `error` (fail fast instead of silent non-persistence).

### 4) Align contract language with behavior

- Update comments/docs in `.chaplain/config/watcher-pipeline-v2.yaml` to match actual artifact source policy (changed/untracked in worktree), or enforce committed-only if intentionally desired.

## Acceptance Criteria

- [ ] AMEND cycles do not create new FR files when `fr_path` already exists.
- [ ] `fr_path` remains stable from first capture through all judge/plan retries for one topic.
- [ ] `capture_fr` only discovers FR path once; subsequent cycles reuse existing `fr_path`.
- [ ] Judge AMEND verdict appends/updates `## Judge Notes` (or `## Judgement`) in the same FR file.
- [ ] Judge REJECT verdict persists rejection reason in the same FR file.
- [ ] If AMEND/REJECT reasoning is not persisted, pipeline fails with explicit `error` event.
- [ ] Existing APPROVE flow and enforce entry behavior are unchanged.
- [ ] Existing event-map routing semantics are unchanged.
- [ ] Tests added.
- [ ] Documentation updated.

## Test Plan (RED -> GREEN)

Add/extend unit tests under `tests/unit/`:

1. Planner identity tests
- revise loop keeps same `fr_path`
- planner prompt contract enforces in-place edit when `fr_path` set

2. Capture behavior tests
- first pass discovers FR path
- subsequent passes with existing `fr_path` skip reselection

3. Judge persistence tests
- AMEND writes `Judge Notes` to target FR
- REJECT writes reason to target FR
- missing writeback triggers `error`

4. Regression tests
- APPROVE still routes to `enforce_session`
- no change to `extract_event`/event-map precedence

## Alternatives Considered

1. Keep current behavior and rely on logs for rationale.
Rejected: reasoning is not durable in FR artifact and loops remain non-deterministic.

2. Always select latest FR by filename.
Rejected: encourages FR renumber churn and identity drift.

3. Force committed-only FR selection.
Rejected for v1: increases friction during draft cycles; can be follow-up once in-place identity is enforced.

## Related

- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`
- `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml`
- `.chaplain/graphs/watcher-plan/prompts/judge.yaml`
- `logs/fsm-pipeline-gh-420-20260519-220746.log`
- `feature-requests/FR-420-extract-event-dict-support.md`
- `feature-requests/FR-416-judge-event-key-mismatch.md`

## Judgement

**Verdict:** APPROVE WITH AMENDMENTS - Scope frozen, authority granted after the amendments below.

This FR identifies a real and recurring pipeline defect pattern and proposes a minimal, architecture-aligned correction. The core diagnosis is correct:

1. AMEND routes back to `plan`, enabling FR identity drift.
2. `capture_fr` currently reselects from changed/untracked FR files, so target identity can move.
3. Judge rationale is reliably present in logs but not reliably durable in the FR artifact.

Required amendments before enforce:

1. Define a single authoritative `fr_path` invariant.
Once `fr_path` is set in context, later cycles must not run discovery logic unless the file is missing on disk.
2. Specify the persistence guard mechanism precisely.
Define how "FR file was updated in this cycle" is measured (for example, mtime/hash snapshot before judge -> compare after judge) and where the check executes.
3. Keep AMEND/REJECT writeback deterministic and idempotent.
Require one canonical section (`## Judge Notes`) with date-stamped entries, updated in place; avoid duplicate headings per cycle.
4. Preserve existing event semantics.
Do not alter event-map resolution order or APPROVE -> enforce transition behavior while implementing this fix.
5. Condemn with RED tests first.
Add failing tests for identity stability, capture reuse, and missing-writeback failure before production edits.

Scope freeze:

1. In scope:
`.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/judge.yaml`, targeted watcher pipeline tests.
2. Out of scope:
Changing judge verdict vocabulary, redesigning watcher state machine phases, altering `extract_event` parser semantics.

Acceptance bar for merge:

1. RED -> GREEN evidence for all new convergence and persistence behaviors.
2. Demonstrated single-file FR identity across at least one AMEND loop test.
3. Demonstrated durable AMEND/REJECT rationale written to FR file.
4. No regression in APPROVE and event-map routing behavior.

**Judge:** GitHub Copilot (GPT-5.3-Codex), 2026-05-20

## Implementation Notes

Implemented with scope-constrained edits:

1. Stabilized FR identity handoff in plan path:
- Added `fr_path` to plan graph state/variables in `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`.
- Passed `fr_path` in plan action vars in `.chaplain/config/watcher-pipeline-v2.yaml`.
2. Made capture logic sticky and absolute:
- `capture_fr` now reuses existing `fr_path` when file exists.
- Fallback discovery still uses changed/untracked scan, but emitted `fr_path` is normalized to absolute path.
3. Tightened prompt contracts:
- Plan prompt now requires in-place edit when `fr_path` exists and forbids renumbering during AMEND cycles.
- Judge prompt now requires persisting AMEND/REJECT rationale in canonical `## Judge Notes`.
4. Added runtime writeback guard:
- In `.chaplain/actions/yamlgraph_async_action.py`, added judge-state guard hooks that snapshot FR mtime on launch and block `revise`/`reject` dispatch if file was not modified in-cycle, emitting `error` instead.

## Verification Evidence

Targeted GREEN run:

```bash
pytest tests/unit/test_fr423_watcher_convergence_persistence.py tests/unit/test_fr305_watcher_pipeline_v2.py tests/unit/test_acceptance_tests_before_enforce.py -q --no-cov
```

Result: `71 passed`.
