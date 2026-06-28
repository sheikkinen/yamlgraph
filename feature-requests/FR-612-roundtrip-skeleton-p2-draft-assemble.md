# Feature Request: Round-trip skeleton P2 — scene_type-dosed draft + deterministic assemble

**Priority:** HIGH
**Type:** Feature
**Effort:** 1 day
**Requested:** 2026-06-28
**Status:** Re-judged after Decision fold — Authority SUSTAINED, corrections resolved (2026-06-28)

## Summary

Produce one prose draft per chapter, dosed by the brief's `scene_type`, then concatenate them
with **no whole-book LLM**. First whole story from the skeleton. Phase 2 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Proves the affect-dose control end to end: reactive chapters foreground interior, proactive
chapters spend feeling in action — the whole reason scene_type is authored on the brief.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED with corrections.** Authority gate for Phase 2.

**Claims verified.** `examples/demos/novel_generator/prompts/prose/generate_beat.yaml` exists and
carries the action-biased default the FR describes. The FR-492 deterministic Book-compose
(no whole-book LLM) is the right assemble pattern; the dose-by-`scene_type` clause is the
payload that makes P1's authored field do work.

**Correction 1 (PRIMARY).** The dose-contrast DoD is eyeball/N=1. Acceptable as a **P2** DoD
**only** because P3 converts it to a number and P4 proves it moves. Make explicit that P2 does
**not** claim the dose is *correct* — only that contrast is *visible*. The number that proves
dose-control is P4's, not P2's; otherwise P2 risks declaring victory on an unmeasured eyeball
(the demo trap this whole skeleton exists to escape).

**Correction 2 (secondary).** `assemble_book` concatenates `chapter_drafts` "by chapter_id", but
map fan-in order is **not** guaranteed. Sort explicitly by a total `chapter_id` order inside the
leaf; do not rely on `collect` ordering, or the deterministic-assembly AC is silently violated.

**Frozen scope.** Readable multi-chapter `book` via a deterministic no-LLM concat (explicit
chapter ordering); visible — not validated — dose contrast. Only leaf tools are Python.

## Decision fold (2026-06-28) — the gate measures the plan, so P2 stays visible-not-validated

Under decision (a) the P3 gate measures the **authored briefs'** closure, not this prose. So P2's
dose contrast remains an **eyeball** signal by design — P2 claims the contrast is *visible*, never
that it is *correct*. The number that validates dose-control is P4's `authored_dangling_rate` move;
whether the prose actually delivers the authored dose is P5's prose-vs-plan check
([FR-615](FR-615-roundtrip-skeleton-p5-roundtrip-closure.md)). Resolves Judge Correction 1 by
naming exactly which later phase carries the proof.

## Re-Judgement (2026-06-28)

**Authority SUSTAINED.** Correction 1 resolved precisely: P2 stays *visible-not-validated* and
names P4 (`authored_dangling_rate`) and P5 (prose-vs-plan) as the proof carriers, so P2 cannot
declare victory on an unmeasured eyeball. Correction 2 (deterministic chapter ordering) remains
unaddressed — bind it: sort `chapter_drafts` by a total `chapter_id` order inside the leaf, never
rely on map `collect` order, or the deterministic-assembly AC is silently violated. Otherwise
sustained.

**Pass 2 (2026-06-28).** Correction 2 is now resolved in the design-of-record
[architecture-walking-skeleton.md](../docs/architecture-walking-skeleton.md) §2: `assemble_book`
"concatenate `chapter_drafts` in explicit `chapter_id` order" — the total-order sort is named, not
left to `collect`. Authority SUSTAINED, no open corrections.

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
