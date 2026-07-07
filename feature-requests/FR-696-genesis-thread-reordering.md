# Feature Request: FR-696 — Genesis Reordering: Thread Extraction Before Structuring

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed (conditional — go/no-go decided by FR-691's 1a/1b diff)
**Effort:** 1 day
**Requested:** 2026-07-07
**Depends:** FR-691 (the 1a/1b diff is this FR's evidence)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 7 of 7, Future Work)

## Summary

Move thread extraction into genesis itself: insert a threads node between `synopsis` and `structure` in `genesis.yaml`, so entities are generated *against* a thread skeleton instead of threads being excavated from entities afterward.

## Value Statement

Future canons are born with antagonistic structure — the `conflict_dissolution_bias` defect is prevented at the boundary where plot information enters, not repaired downstream.

## Problem

Gen 3 genesis shreds the synopsis's plot information into per-entity fields; FR-691 re-mines it downstream — a `downstream_fix` tolerated only because the Floodmark canon already exists. For new canons, normalization belongs at the entry boundary (`the_one_law`).

## Go/No-Go Condition

FR-691's acceptance criteria include a documented raw read of the 1a/1b diff:

- **Go**: 1b (canon-grounded) adds substantial plot the synopsis-only pass missed → entity generation genuinely contributes threads → reordering must preserve a post-entity reconcile pass too.
- **No-go / simplify**: 1b adds little beyond id-grounding → threads are fully determined at the synopsis boundary → a single extraction node before structuring suffices and downstream mining is deleted.

This FR is not Judged until that verdict is written into FR-691.

## Proposed Solution (sketch, pending condition)

1. Insert `extract_threads` node in `examples/novel_fandom/genesis.yaml` after `synopsis`, before `structure`; persist `story/thread/*.yaml` as the first derived artifacts.
2. Entity-generation prompts receive the thread list; the FR-692 admission rule (`pressurizes` citation) applies at genesis time for dynamic entities.
3. Rerun genesis on a fresh premise; compare the newborn canon's thread gates against Floodmark's retrofit path.

## Acceptance Criteria

- [ ] Go/no-go verdict cited from FR-691's 1a/1b diff read
- [ ] Genesis emits gated threads before entity structuring; all FR-691 gates pass on a fresh-premise run
- [ ] Fresh canon has zero latent threads without waivers at birth (vs Floodmark's retrofit count, recorded for comparison)
- [ ] Tests tagged; changelog fragment; demo output

## Alternatives Considered

- **Keep extraction purely downstream (FR-691 as permanent architecture)** — acceptable if the no-go verdict lands; this FR is then closed as rejected with the diff as rationale.

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md (Future Work: Genesis Reordering)
- Diary: diary-2026-07-06-the-dropped-plot-layer.md
- Depends: FR-691 verdict; touches FR-655 (genesis pipeline), FR-692 (admission rule)
