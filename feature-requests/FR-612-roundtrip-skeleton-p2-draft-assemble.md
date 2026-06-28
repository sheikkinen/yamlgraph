# Feature Request: Round-trip skeleton P2 — scene_type-dosed draft + deterministic assemble

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-28

## Summary

Produce one prose draft per chapter, dosed by the brief's `scene_type`, then concatenate them
with **no whole-book LLM**. First whole story from the skeleton. Phase 2 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Proves the affect-dose control end to end: reactive chapters foreground interior, proactive
chapters spend feeling in action — the whole reason scene_type is authored on the brief.

## Problem

novel_generator's `generate_beat` map hard-codes an action-biased default ("show emotions
through action", "end with tension"). That default is correct for proactive scenes and wrong
for reactive ones. The draft node must take the dose from the brief, not from a fixed prompt.

## Proposed Solution

- `draft_chapter` (map over `briefs`): new prompt `prompts/roundtrip/draft_chapter.yaml`,
  reusing the novel_generator
  [`generate_beat.yaml`](../examples/demos/novel_generator/prompts/prose/generate_beat.yaml)
  map structure. Inputs = the brief + the cast sheets for `brief.cast` + a **scene_type
  affect-dose clause** (proactive → interior sparingly, feeling spent in action; reactive →
  interior foregrounded, reaction→dilemma→decision). `collect: chapter_drafts`.
- `assemble_book` (python leaf in `nodes/tools.py`): ordered concat of `chapter_drafts` by
  `chapter_id` → `book`. Deterministic, no LLM (dungeon_master FR-492 Book-compose pattern).

## Acceptance Criteria

- [ ] `book` is a readable multi-chapter draft assembled in chapter order.
- [ ] Reactive chapters visibly carry more interior than proactive chapters (eyeball dose
      contrast on N=1 genre).
- [ ] Assembly is a deterministic no-LLM leaf tool.
- [ ] Only leaf tools are Python; graph lints and runs end-to-end.

## Alternatives Considered

Whole-book single-LLM compose — rejected per FR-492 (no whole-book LLM). Per-beat drafting
(finer than per-chapter) — deferred to a later phase only if the gate shows chapter-level
drafting loses beats.

## Related

- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P2)
- Predecessor: FR-611 (P1). Successor: FR-613 (P3 coherence gate)
