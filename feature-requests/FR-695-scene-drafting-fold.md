# Feature Request: FR-695 — Scene Drafting (Sequential Fold)

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 1–2 days
**Requested:** 2026-07-07
**Depends:** FR-694 (chapter plan — drafting consumes the gated plan)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 6 of 7)

## Summary

Draft chapters sequentially (fold, not parallel map) with a rolling story-so-far summary, writing prose to `story/drafts/`. Per-chapter context: chapter plan entry + relevant canon slice + rolling summary, kept under 50k tokens.

## Value Statement

The pipeline produces actual prose — the artifact the whole canon exists to serve — with voice continuity that parallel drafting cannot provide.

## Problem

Parallel map over chapters (the obvious YAMLGraph pattern) produces voice drift and continuity breaks: chapter N cannot know what chapter N−1 revealed or withheld. Identified in plan review as the map-node anti-fit for prose.

## Proposed Solution

Graph `examples/novel_fandom/scene_draft.yaml`:

1. Sequential loop over chapter plan entries (loop-limited per doctrine).
2. Per chapter, two nodes: **draft** (plan entry + canon slice for its event/character ids + rolling summary → prose) and **summarize** (prose → updated rolling summary: revealed facts, open questions, emotional temperature).
3. Persist each chapter to `story/drafts/ch-NN.md` as produced (resume via `skip_if_exists`).
4. Context budget asserted <50k tokens per call; canon slice selected by the chapter's cited ids, not full canon.

Review is by reading (`read_raw_output_first`): no prose-quality metric is built; acceptance is a human/Judge read of the drafts against the chapter plan's thread ops.

## Acceptance Criteria

- [ ] All chapters drafted sequentially; reruns resume from last persisted chapter
- [ ] Rolling summary present and consumed (test: chapter N prompt contains summary of N−1)
- [ ] Context per call <50k tokens (asserted in test)
- [ ] Raw read of ≥3 drafted chapters cited in FR review: thread ops from the plan visibly enacted in prose
- [ ] Tests tagged; changelog fragment; demo output

## Alternatives Considered

- **Parallel map over chapters** — rejected: voice drift, no continuity of revelation.
- **Single mega-prompt whole-book draft** — context blowout and no resume granularity.

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Depends: FR-694
