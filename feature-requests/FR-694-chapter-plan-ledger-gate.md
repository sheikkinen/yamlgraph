# Feature Request: FR-694 — Chapter Plan with Thread Ledger Gate

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-07-07
**Depends:** FR-693 (event revision — chapters plan over the closed event set)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 5 of 7)

## Summary

Generate `story/chapter_plan.yaml` — chapters with `act: int`, event ids, POV, thread operations (raise/escalate/release per thread id) — validated by a Python ledger gate ported from `dungeon_master/api/plot/validate.py`. LLM writes, Python judges.

## Value Statement

The book's structure becomes a checkable artifact: de-escalation, orphaned threads, and off-page climaxes fail a script before a single scene is drafted.

## Problem

Without a chapter plan gated on the thread ledger, drafting (FR-695) inherits the Gen 3 failure mode: chapters that read plausibly while every conflict quietly dissolves (`conflict_dissolution_bias`). The Gen 2 CLOSED AFFECT invariant proved this class of defect is mechanically checkable.

## Proposed Solution

1. **Schema**: `ChapterPlan` Pydantic model — chapters with `act: int` (1–3), ordered event ids (must respect `sequence`), POV character id, `thread_ops: [{thread_id, op: raise|escalate|release}]`.
2. **LLM node**: full canon + threads + throughlines + waivers → chapter plan.
3. **Ledger gate** (Python, ported from `dungeon_master/api/plot/validate.py`), fails on:
   - release without a prior raise for the same thread
   - open-thread count decreasing monotonically before the first `act: 3` chapter (premature de-escalation)
   - any non-waived thread never released
   - chapter content contradicting canon (event id in a chapter whose POV character is not a participant, events out of `sequence` order)
4. Persist-then-fail: the plan artifact is always written; the gate verdict is separate (evidence before verdict).

## Raw Output Read

The ledger gate is measurement tooling — per Scripture, Judgement is withheld until the FR evidences a raw read of `chapter_plan.yaml`: N chapters read end-to-end with concrete surprising details cited, before any gate statistics are trusted. To be filled at Enforce time.

## Acceptance Criteria

- [ ] `ChapterPlan` schema + ledger gate script with tests (RED first: fixtures for each failure class above)
- [ ] Generated chapter plan for Floodmark passes all gate checks
- [ ] Raw Output Read section completed with cited chapter details before Judgement
- [ ] Climax (flood, Arnulf's release) verified on-page: covered by `act: 3` chapters with release ops
- [ ] Tests tagged; changelog fragment; demo output

## Alternatives Considered

- **LLM self-grading of the plan** — rejected in plan review: self-graded tension ledger is `gate_checks_shape_not_substance`; the judge must be Python.

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Ancestor: `dungeon_master/api/plot/validate.py`, `tests/test_plot_affect_closure.py` (Gen 2)
- Depends: FR-690–693; Blocks: FR-695
