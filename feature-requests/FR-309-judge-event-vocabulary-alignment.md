# Feature Request: FR-309 Judge Event Vocabulary Alignment

**Priority:** CRITICAL
**Type:** Bug
**Status:** Approved
**Effort:** 0.25 days
**Requested:** 2026-05-02

## Summary

Align the judge prompt verdict vocabulary (`APPROVE`/`AMEND`/`REJECT`/`SPLIT`) with the pipeline event_map (`APPROVE`/`REVISE`/`REJECT`) so the FSM routes judge verdicts correctly.

## Value Statement

The watcher pipeline's judge gate becomes functional — verdicts from the LLM actually drive state transitions instead of silently falling through to auto-approve.

## Problem

During the gh-264 pipeline run, the judge completed in 8 seconds and auto-approved without reviewing. Root cause analysis traced the failure chain:

### A. Vocabulary mismatch

The judge prompt (`.chaplain/graphs/copilot/prompts/judge.yaml`) instructs the LLM to output one of:
- `APPROVE`, `AMEND`, `REJECT`, `SPLIT`

The pipeline event_map (`.chaplain/config/watcher-pipeline-v2.yaml`) scans stdout for:
- `APPROVE` → `approve`, `REVISE` → `revise`, `REJECT` → `reject`

Two mismatches:
1. Prompt says `AMEND`, event_map expects `REVISE` — judge amendment verdicts never match
2. Prompt says `SPLIT`, event_map has no mapping — split verdicts never match

Any non-matching verdict falls through to `success: approve` (auto-approve).

### B. session_id not propagated to enforce

The `plan_done` event defines `context_map: { session_id: payload.session_id }`, but `yamlgraph_async` returns a plain event string (e.g. `"plan_done"`), not a structured payload. The FSM engine receives no `payload.session_id`, so `context.session_id` remains unset. The enforce graph's `resume: "{session_id}"` resolves to the literal string `"{session_id}"` or empty, causing copilot CLI to start a fresh session instead of resuming.

## Proposed Solution

### Fix A: Align vocabularies (normalize at the boundary)

**Option chosen:** Update event_map to match prompt vocabulary. The prompt is the source of truth for the LLM — changing event_map is cheaper and less error-prone than retraining LLM behavior.

In `.chaplain/config/watcher-pipeline-v2.yaml`:
```yaml
judge:
  - type: yamlgraph_async
    event_map:
      APPROVE: approve
      AMEND: revise      # was: REVISE
      REJECT: reject
      SPLIT: revise      # new: treat SPLIT as revise (re-plan with sub-topics)
    success: error        # FR-308: no-match = fail, not approve
```

Add FSM transition for the `revise` event (already exists — judge→plan).

### Fix B: Propagate session_id from yamlgraph_async

In `yamlgraph_async_action.py`, after a successful yamlgraph run, parse the `_display_result` output for `session_id` and include it in the returned event payload. Alternatively, remove the `session_id` context_map from `plan_done` and let enforce start a fresh session (simpler, acceptable for v2).

**Option chosen (v2 simplicity):** Remove `session_id` from `plan_done` context_map and from enforce graph's `cli_flags.resume`. Enforce runs a fresh session. Session continuation is a v3 optimization.

## Acceptance Criteria

- [ ] **AC-01:** Judge event_map contains `AMEND: revise` and `SPLIT: revise`
- [ ] **AC-02:** Judge event_map does NOT contain `REVISE` (removed, vocabulary aligned to prompt)
- [ ] **AC-03:** Judge `success` is `error` (not `approve`) — FR-308
- [ ] **AC-04:** `plan_done` event has no `context_map` for `session_id` (removed)
- [ ] **AC-05:** Enforce graph does not use `resume` cli_flag (removed)
- [ ] **AC-06:** Existing pipeline unit tests updated and passing
- [ ] **AC-07:** `yamlgraph graph lint` passes on both judge and enforce graphs
- [ ] **AC-08:** When judge stdout contains `SPLIT`, FSM transitions judge→plan (via revise event)
- [ ] **AC-09:** Enforce graph's copilot node has no `resume` in cli_flags

## Alternatives Considered

1. **Change prompt vocabulary to match event_map** — Rejected. The prompt is a natural-language instruction to the LLM; `AMEND` is clearer than `REVISE` in the judge context. Normalize at the boundary (event_map), not downstream (prompt).
2. **Add structured payload output to yamlgraph_async** — Deferred to v3. Requires parsing graph state output, which couples the action to yamlgraph internals.
3. **Use regex matching in event_map** — Over-engineering for 4 fixed tokens.

## Related

- Root cause of: FR-306 (gh-264 pipeline failure)
- Safety net: FR-308 (judge fallback must fail)
- Observability: FR-307 (yamlgraph_async logging)
- Parent: FR-305 (pipeline FSM v2)
- Files:
  - `.chaplain/config/watcher-pipeline-v2.yaml` (event_map + context_map)
  - `.chaplain/graphs/watcher-enforce/enforce-session.yaml` (remove resume flag)
  - `.chaplain/graphs/copilot/prompts/judge.yaml` (no changes — source of truth)
