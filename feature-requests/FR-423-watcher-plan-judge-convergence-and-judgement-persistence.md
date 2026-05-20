# Feature Request: FR-423 Watcher Plan/Judge Convergence and Judgement Persistence

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
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
