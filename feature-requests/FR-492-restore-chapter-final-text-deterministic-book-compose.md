# Feature Request: FR-492 — Restore Per-Chapter Final Text; Compose the Book Deterministically

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-06-16
**Regime:** FR-474 J3 (DM prototype) — no CAP/REQ/CI-gates/changelog; diary required.

## Summary

FR-491 retired the three single-scene finishes (`final_cut`, `final_cut_turns`,
`walkthrough`) and replaced them with one LLM `book.yaml` pass that composes the
whole manuscript from per-chapter *recaps*. That collapse swept up a capability
the book pass does not replace: `final_cut`'s **plot-fidelity** (follow the
chapter's prescripted beats in detail) and its **final text** (the chapter's
actual polished prose, not a recap summary). This FR restores a per-chapter
final-text step and makes the first book "generation" a **deterministic,
LLM-free composition** of those chapter texts — moving the generative load off
the single overloaded seam where the empty-book token bug lived. Later
continuity/voice passes remain LLM, driven by verification (phase 2, out of
scope here).

## Value Statement

The book is composed from faithful, full-text chapters by deterministic
assembly, so the first draft is reproducible and free, plot-fidelity is checked
where it is cheap (per chapter), and the fragile whole-book LLM seam is no longer
on the critical path to *any* output.

## Problem

Three concrete defects in the FR-491 end state:

1. **Lost plot-fidelity.** `final_cut` consumed canonical `beats` + phase-tagged
   `arc` + `climax` under "preserve every canonical BEAT." `close_chapter` keeps
   none of that — a chapter's stored `text` is `chapter_recaps_text(doc, cid)`,
   the concatenated turn recaps. No beat is verified present.
2. **Recap register, not final text.** The book pass is handed summary-register
   recaps and asked to elevate them into prose *and* stitch the arc in one LLM
   call — the most overloaded node in the graph.
3. **The only path to a book is a fragile generative seam.** That same node
   returned an empty string when Gemini's hidden thinking consumed the token
   budget (FR-491 live witness: `completion_tokens=3996, book=""`). Composition
   of already-final chapter texts is structural assembly — it should not be a
   generative step at all.

See `docs/diary/diary-2026-06-16-the-capability-pruned-with-the-duplication.md`
for the retrospective: an N→1 collapse is safe only when each of the N was
redundant *with the survivor*, not merely with each other.

## Proposed Solution

Two layers, ordered by verifiability. **Layer A is generative (LLM, chapter
scope); Layer B is deterministic (no LLM).**

### Layer A — Restore per-chapter final text (`chapter_final.yaml`)

Reinstate the `final_cut` prompt at **chapter** scope (not the retired
single-Key-Scene scope). When a chapter's scene completes, in addition to (or
in place of) storing raw recaps, run a chapter-final compose that follows the
chapter's prescripted plot in detail and emits the chapter's polished final
prose.

Inputs (chapter-scoped analogues of the retired `final_cut` inputs):

```yaml
# prompts/chapter_final.yaml (restored from final_cut, re-scoped)
# scene plan  -> the chapter summary (the intended arc / destination)
# arc         -> this chapter's played recaps in order (phase-tagged)
# beats       -> the chapter's canonical beats (derive from summary or director)
# climax      -> the chapter's climax turn (from director phase tags)
# draft/instr -> revision side-channel (unchanged)
```

`close_chapter()` records the returned prose as the chapter card's `text`
(replacing `text: recaps`). `world_state` derivation is unchanged. The chapter
`text` is now *final text*, beat-faithful — exactly what `final_cut` produced,
per chapter.

### Layer B — Deterministic book composition (no LLM)

Replace the first book "generation" with a pure function that assembles the
chapter final texts into one manuscript. No model call.

```python
# chapter_ops.compose_book_deterministic(doc) -> str  (pure, no LLM)
#   for each cid in chapters.order:
#     "# Chapter {index}: {title}\n\n{card.text}"        # the final text
#   joined by a blank line; optional world-state interstitials suppressed
#   in the reader manuscript (they remain the close-chapter ledger).
#   Raises if no chapter is played (Commandment 6 — same contract as today).
```

The Book stage's first render calls `compose_book_deterministic` (free,
reproducible, never empty when chapters exist). The existing `book.yaml` LLM
pass is **demoted to an optional revision pass** (it already accepts
`draft` + `instruction`): the deterministic composition seeds `draft`, and any
later continuity-unification / voice pass operates on it. The model is no longer
on the path to a *first* book.

### Phase 2 (noted, out of scope for this FR)

Verification-driven revision: compose → check continuity (forward-carry honored,
no fact contradicted, no chapter invented) → revise on the failing check →
re-check. Uses the `verification` primitive and realizes the Scripture seed
`verification_checkpoint_primitive`. Tracked separately.

## Rollback note

This is partially a **rollback** of FR-491 Slice 4 (`4040fac0`): the
`final_cut` prompt's *content and fidelity contract* are restored (re-scoped to
chapters). It is **not** a revert — the chapter-play architecture, forward-carry,
and the retirement of `final_cut_turns` / `walkthrough` / `staging` all stand.
Restore the prompt from history rather than rewriting:

```bash
git show 4040fac0^:examples/dungeon_master/prompts/final_cut.yaml \
  > examples/dungeon_master/prompts/chapter_final.yaml
# then re-scope variable names: key_scene->summary, scene/turn->chapter
```

## Acceptance Criteria

- [ ] `prompts/chapter_final.yaml` restored from `final_cut` (4040fac0^), re-scoped
      to chapter inputs (summary as plan, this chapter's recaps as arc, chapter
      beats, chapter climax).
- [ ] `chapter_final.yaml` graph added; `yamlgraph graph lint` clean. Token regime
      matches a long-form node (bounded `thinking_budget`, generous `max_tokens` —
      see FR-491 book fix), not the uniform 4000 default.
- [ ] `close_chapter()` stores beat-faithful final prose as the chapter card
      `text` (not raw recaps); `world_state` derivation unchanged.
- [ ] `chapter_ops.compose_book_deterministic(doc)` — pure, no LLM; orders chapters
      by `chapters.order`; raises on no played chapter (Commandment 6); unit-tested
      with a fixture doc (no model).
- [ ] Book stage's first render uses the deterministic composition; `book.yaml`
      LLM pass demoted to an optional revision pass seeded by `draft`.
- [ ] A book is produced with **zero** LLM calls given played chapters (proven by
      a test that asserts no graph invocation on the compose path).
- [ ] DM suite green; ruff + lint-imports + vulture clean.
- [ ] Live vertex witness: chapters carry beat-faithful final text; the book
      assembles deterministically and is non-empty without the whole-book LLM call.
- [ ] Diary reflection + Seed (the `prune_overshoot` heuristic).
- [ ] FR-491 doc cross-referenced (the capability this restores).

## Alternatives Considered

- **Keep the single LLM book pass, just fix the token budget (status quo after
  FR-491 book fix).** Rejected: it works but leaves plot-fidelity unverified and
  keeps the only path to a book on a fragile generative seam. The reviewer's
  point stands — composition of final texts is assembly, not generation.
- **Deterministic composition straight from recaps (skip Layer A).** Rejected:
  concatenated recaps are summary register, not final text; the manuscript would
  read as stapled summaries. The chapter-final step is what makes deterministic
  assembly produce readable prose.
- **One big LLM pass that also does per-chapter fidelity.** Rejected: that is the
  current overload. Fidelity belongs where it is locally checkable (chapter), not
  globally entangled with arc-stitching.

## Related

- FR-491 (`4040fac0`) — retired the finishes; this restores the pruned capability.
- `examples/dungeon_master/api/chapter_ops.py` — `close_chapter`, `played_chapters_text`, `compose_book`.
- `examples/dungeon_master/prompts/final_cut.yaml` (at `4040fac0^`) — the prompt to restore.
- `examples/dungeon_master/book.yaml` / `prompts/book.yaml` — demoted to revision pass.
- `docs/diary/diary-2026-06-16-the-capability-pruned-with-the-duplication.md` — the rationale.
- Scripture seed `verification_checkpoint_primitive` — phase 2 driver.
