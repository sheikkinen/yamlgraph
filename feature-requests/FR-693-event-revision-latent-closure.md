# Feature Request: FR-693 — Event Revision for Latent-Thread Closure

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1–2 days
**Requested:** 2026-07-07
**Depends:** FR-692 (world pressure — new carriers must exist before events can use them)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 4 of 7)

## Summary

Agent pass that closes latent threads by adding events: every `status: latent` thread either gains raise/release events in canon or receives an explicit waiver in `story/thread_waivers.yaml`. Additive-only; existing event files byte-identical.

## Value Statement

Arnulf's three off-page days, Heidrun's plot-solvent interventions, and the young men who never act become on-page events — or documented, deliberate omissions.

## Problem

FR-691's reconcile step will surface latent threads (mined from fears, internal tensions, rules) with empty `raises`/`releases`. A thread with no events is a promise the book never keeps. Currently 19/22 events cluster at year 0 and the three known story gaps (Arnulf off-page, Heidrun as solvent, passive young men) have no event coverage.

## Proposed Solution

Agent graph `examples/novel_fandom/event_revision.yaml`:

1. Input: threads + throughlines + canon. The deficit list = latent threads and threads whose `raises` outnumber their `releases` asymmetrically.
2. For each deficit: create events via the FR-658 `create_event` tool (dedup + ref_check apply), assigning `sequence` values in the gaps left by FR-690's sparse numbering. **Scope inherited from FR-690's Judgement:** teach `create_event`'s inline schema/prompt the `sequence` field — new events must emit it.
3. **Waiver path**: deficits deliberately left open recorded in `story/thread_waivers.yaml` (thread id, reason, decided-by) — the plan's exit gate is *zero unwaived latents*, not zero latents.
4. **Byte-identity gate**: `git diff --exit-code` on pre-existing event files — revision is additive-only; new files only.
5. Rerun FR-691 gates: ledger walk must now pass for every non-waived thread.

## Acceptance Criteria

- [ ] Exit gate: zero latent threads without waiver entries; waiver file `ref_check`ed against the current thread set
- [ ] Pre-existing event files byte-identical (`git diff --exit-code` in test, RED first with a mutating fixture)
- [ ] New events carry unique `sequence` values consistent with `year` ordering
- [ ] Ledger walk passes for all non-waived threads after revision
- [ ] Tests tagged; changelog fragment; demo output

## Alternatives Considered

- **Rewrite existing events to add raises/releases** — violates canon-grows-never-changes; blame and revert become impossible.
- **Force zero latents (no waivers)** — some latents are texture, not defects; forcing closure invents events nobody wants (`growth_as_default`).

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Depends: FR-690, FR-691, FR-692; Blocks: FR-694
