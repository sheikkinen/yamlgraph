# Feature Request: FR-492 — Restore Per-Chapter Final Text; Compose the Book Deterministically

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — scope frozen (2026-06-16)
**Effort:** 3 days
**Requested:** 2026-06-16
**Regime:** FR-474 J3 (DM prototype) — no CAP/REQ/CI-gates/changelog; diary required.
**Archive:** current book-compose implementation preserved at tag
`archive/dm-slice4-book-compose` (HEAD `04238f32`) before any rollback.

## Summary

FR-491 retired the three single-scene finishes (`final_cut`, `final_cut_turns`,
`walkthrough`) and replaced them with one LLM `book.yaml` pass that composes the
whole manuscript from per-chapter *recaps*. That collapse swept up a capability
the book pass does not replace: `final_cut`'s **plot-fidelity** (follow the
chapter's prescripted beats in detail) and its **final text** (the chapter's
actual polished prose, not a recap summary). This FR archives the current
book-compose implementation, takes a **full Slice 4 rollback** as the baseline to
recover the finish subsystem intact, re-scopes `final_cut` to chapter scope, and
makes the first book "generation" a **deterministic, LLM-free composition** of
those chapter texts — moving the generative load off the single overloaded seam
where the empty-book token bug lived. Later continuity/voice passes remain LLM,
driven by verification (Phase 4, out of scope here).

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

**Strategy change (replan).** The original surgical plan — "copy the retired
`final_cut.yaml` prompt and re-scope its variable names" — is unsound. `final_cut`
is not a free-standing prompt: its inputs are assembled by `final_cut_context()`,
which depends on two helpers, `climax_turn()` and `parse_beats()`, that Slice 4
**also deleted** (they were inside the 348-line `turn_ops.py` removal). All three
read the **old flat doc shape** (`doc["turns"]`, `doc["key_scene"]`) that the
chapter-play slices have since dismantled — turns now live under
`chapters.cards[<cid>].turns` and `key_scene` no longer exists. A copy-and-rename
restore would import broken dependencies against a shape that is gone.

Instead, take a **full Slice 4 rollback as the baseline**, then adapt forward.
This recovers a self-consistent finish subsystem from history (every helper, its
staging and walkthrough siblings, the tree stages, navigation chain, and session
branch — all internally wired) rather than hand-reconstructing deleted helpers.

### Phase 0 — Archive (done)

Current book-compose implementation tagged `archive/dm-slice4-book-compose`
(`04238f32`). Recoverable file-by-file (`git show archive/dm-slice4-book-compose:<path>`)
or wholesale. The LLM `book.yaml` graph lives on there for the Phase 4 voice pass.

### Phase 1 — Full Slice 4 rollback (baseline, committed RED)

Revert `4040fac0` to restore the entire finish subsystem and remove the
whole-book LLM compose:

- **Restored graphs + prompts:** `final_cut`, `final_cut_turns`, `walkthrough`,
  `staging` (both the example-root graph and the `prompts/` template each).
- **Restored `turn_ops.py` machinery:** `climax_turn`, `parse_beats`,
  `final_cut_context`, `invoke_final_cut`, `validate_cut_turns`,
  `render_cut_turns`, `invoke_final_cut_turns`, `_cut_spine`,
  `walkthrough_render_inputs`, `walkthrough_staging_context`,
  `invoke_walkthrough_staging`, `render_walkthrough`, `_ordered_render_texts`,
  `invoke_walkthrough`.
- **Restored `tree.py`:** `scene_is_complete`, `cut_present`, the three finish
  Stage entries/constants.
- **Restored navigation:** the `final_cut → final_cut_turns → walkthrough` accept
  chain; **restored session** `_compose_special` finish branches.
- **Removed:** `book.yaml`, `prompts/book.yaml`, `chapter_ops.compose_book`,
  `chapter_ops.played_chapters_text`, the Book Stage / gate / navigation /
  session Book branch and tests.

The revert conflicts modify/delete on `book.yaml` (it was edited by `2abb8483`
and `eb31bc63` after Slice 4) — resolve by taking the **deletion** (book.yaml
leaves in the rollback; its content is preserved in the archive tag).

This baseline is **RED**: the restored finish code reads `doc["turns"]` /
`doc["key_scene"]`, which the chapter-play shape no longer provides. Commit it as
the explicit RED starting point (a faithful, internally-consistent recovery), per
the RED→GREEN discipline — the understanding the rollback restores is worth more
than a clean diff.

### Phase 2 — Re-scope `final_cut` to chapter scope (GREEN)

Adapt the restored `final_cut` machinery to operate **per chapter**, then
deliberately re-prune the genuinely-redundant siblings — this time naming where
each deleted thing's capability goes (the diary's `prune_overshoot` discipline):

- `final_cut_context(doc)` → `final_cut_context(doc, cid)`: read
  `chapters.cards[cid].turns` (not flat `doc["turns"]`); the **chapter summary**
  stands in for `key_scene` as the scene plan; `climax_turn` operates within the
  chapter.
- **Beats are re-sourced, not re-parsed (reflection amendment).** The restored
  fidelity path `parse_beats(key_scene)` is **inert on chapters**: it extracts a
  `BEATS:` block from a frozen key-scene card, and a chapter has only a free-text
  `summary` (turn_ops.py L288 already concedes this). A mechanical re-scope would
  restore the prose but silently drop the fidelity — the exact `plausible_wrong_answer`
  the diary warns of. Instead, harvest the **`beats_satisfied`** the director
  already accumulates per turn (`_canonicalize_beats`, L285): the play loop
  records what the finish needs. `final_cut_context` unions the chapter's turns'
  `beats_satisfied` (cumulative, order-preserving) as the `beats` variable.
  `parse_beats` is then dead with `key_scene` gone — **retire it** (vulture will
  flag it otherwise).
- `close_chapter()` runs the re-scoped final_cut and stores the returned
  beat-faithful prose as the chapter card's `text` (replacing `text: recaps`);
  `world_state` derivation unchanged.
- **Re-prune** `final_cut_turns`, `walkthrough`, `staging` — they were truly
  redundant *with each other* and with the per-chapter final_cut. Destination of
  their capability: the single re-scoped `final_cut` (turn-aligned segmentation
  and staging notes are not needed when the chapter's whole arc composes at
  once). Record this destination in the commit, per the diary Seed.

**Why not a turn-scope finish (reflection).** A per-turn finish was considered and
rejected: a turn already becomes `recap.text` prose via `invoke_turn`, so a
per-turn finish re-creates the recap writer (`false_duplicate`), and it destroys
the finish's only reason to exist — `final_cut` exists to "do two things the
turn-by-turn writer could not": weight the climax and de-repeat standing facts,
both of which require seeing the **whole arc at once**. The finish must operate
*above* the turn or it is redundant. Chapter is the right floor: small enough to
verify one arc's beats, large enough to weight a climax. Determinism belongs at
the **book** seam (Phase 3, already-final inputs); generation belongs at the
**chapter** seam.

### Phase 3 — Deterministic book composition (no LLM)

Reintroduce book assembly as a **pure function** over the chapter final texts —
not the LLM `book.yaml` that the rollback removed:

```python
# chapter_ops.compose_book_deterministic(doc) -> str  (pure, no LLM)
#   for each cid in chapters.order:
#     "# Chapter {index}: {title}\n\n{card.text}"        # the beat-faithful final text
#   joined by a blank line; world-state interstitials stay in the close-chapter
#   ledger, suppressed from the reader manuscript.
#   Raises if no chapter is played (Commandment 6).
```

The Book stage's first render calls this (free, reproducible, never empty when
chapters exist). The model is off the path to a *first* book.

### Phase 4 — LLM voice/continuity passes (noted, out of scope here)

Recover the archived `book.yaml` as an **optional revision pass** (it already
accepts `draft` + `instruction` and returns a full revision): the deterministic
composition seeds `draft`; later passes unify continuity and voice, driven by
verification (compose → check forward-carry honored / no fact contradicted / no
chapter invented → revise on the failing check → re-check). Realizes the Scripture
seed `verification_checkpoint_primitive`. Tracked separately.

## Rollback note

This FR's **baseline is a true rollback** of FR-491 Slice 4 (`4040fac0`) via
`git revert`, not a hand-copied prompt restore. It is still **not** a wholesale
revert of FR-491: the chapter-play architecture and forward-carry from Slices 1–3
stand; the rollback is scoped to the finish subsystem Slice 4 changed, then
Phases 2–3 carry it forward into chapter scope. The pre-rollback book-compose
implementation is preserved at `archive/dm-slice4-book-compose` so nothing is
lost.

```bash
# Phase 0 (done): archived current implementation
git tag -l archive/dm-slice4-book-compose   # -> 04238f32

# Phase 1: full rollback baseline
git revert --no-commit 4040fac0
git rm examples/dungeon_master/book.yaml      # resolve modify/delete: take the deletion
# ... resolve remaining paths, then commit RED:
#   refactor(dm): FR-492 phase 1 roll back slice 4 finish subsystem (RED baseline)
```

**What "RED" means here (false-green warning).** The revert re-adds 564 lines of
finish tests to `test_turn_prototype.py`. These build their **own old-shape**
fixtures inline (`doc["turns"]`, `key_scene`) and use **mock LLMs that return
fixed text regardless of input**, so they pass against the reverted helpers while
proving nothing about the live chapter-play doc (`chapters.cards[cid].turns`, no
`key_scene`). The honest RED is therefore *the absence of a test that drives the
finish from a real chapter-play doc* — not a red suite. **Pytest green after
Phase 1 is not evidence the rollback is correctly in place** (`plausible_wrong_answer`).
Phase 2 must add that missing test FIRST (RED against the re-scoped helper), then
make it pass — the suite-green AC alone is insufficient and must not be trusted as
the Phase 1 gate.

**Churn the user accepted.** A full revert restores `final_cut_turns`,
`walkthrough`, `staging` and their tests, only for Phase 2 to re-prune most of
them — ~560 test lines restored then largely deleted. The cheaper path is a
cherry-pick restore of only `final_cut` + `climax_turn` + `parse_beats` +
`final_cut_context` (+ their 3 pure tests). The user explicitly chose the **full
rollback** as a self-consistent, internally-wired recovery baseline; that intent
stands. This note records the tradeoff so the churn is a decision, not a surprise.

## Acceptance Criteria

- [x] **Phase 0:** current implementation archived at tag
      `archive/dm-slice4-book-compose` (`04238f32`); recovery commands recorded.
- [x] **Phase 1:** `4040fac0` reverted (book.yaml modify/delete resolved by
      deletion); finish subsystem restored intact (graphs, prompts, `turn_ops`
      helpers incl. `climax_turn`/`parse_beats`, `tree` stages, navigation chain,
      session branch); committed as an explicit baseline. **Phase 1 is NOT gated
      on a green suite** (the restored finish tests are false-green: self-built
      old-shape fixtures + fixed-output mocks). Gate Phase 1 only on the revert
      applying and the archive tag existing.
- [x] **Phase 2 (witness test FIRST):** add a test that drives the finish from a
      **real chapter-play doc** (`chapters.cards[cid].turns`, no `key_scene`) —
      committed RED before the re-scope, green after. This is the test the
      rollback's restored suite does not provide; it is the true verification the
      finish is in place. The witness must assert **all four** assembled inputs:
      the arc (every played recap in order), the chapter summary as plan, the
      chapter climax marker, **and non-empty `beats`** (so the restored fidelity
      is condemned-if-missing, not assumed).
- [x] **Phase 2:** `final_cut_context` re-scoped to `(doc, cid)` over
      `chapters.cards[cid].turns`, chapter summary standing in for `key_scene`;
      **`beats` sourced from the director's accumulated `beats_satisfied`**, not
      `parse_beats` (which is inert on free-text chapter summaries); `parse_beats`
      retired. `close_chapter()` stores beat-faithful final prose as the chapter
      card `text` (not raw recaps); `world_state` derivation unchanged. Token
      regime for the final_cut node is long-form (bounded `thinking_budget`,
      generous `max_tokens`), not the uniform 4000 default. The restored old-shape
      finish tests are migrated to the chapter shape or deleted — none left
      asserting against `doc["turns"]`/`key_scene`.
- [x] **Phase 2 re-prune:** `final_cut_turns`, `walkthrough`, `staging` removed
      again, with the commit naming where each one's capability now lives
      (`prune_overshoot` discipline).
- [x] **Phase 3:** `chapter_ops.compose_book_deterministic(doc)` — pure, no LLM;
      orders chapters by `chapters.order`; raises on no played chapter
      (Commandment 6); unit-tested with a fixture doc (no model). Book stage's
      first render uses it. Wired as a seedless, graph-less terminal stage
      (`tree.all_chapters_played` gate + `kind="book"`), reachable via
      `navigation.can_visit` + a "The Book" breadcrumb crumb; `session._view`
      renders the compose on first navigate.
- [x] A book is produced with **zero** LLM calls given played chapters (proven by
      a test asserting no graph invocation on the compose path — `get_app`
      patched to raise, and the seedless stage is never auto-drafted).
- [x] `yamlgraph graph lint` clean; DM suite green (75 passed); ruff +
      lint-imports + vulture clean.
- [ ] Live vertex witness: chapters carry beat-faithful final text; the book
      assembles deterministically and is non-empty without any whole-book LLM call.
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

## Judgement (2026-06-16)

**Verdict: strategy approved, scope frozen with three required refinements (now
folded in).** The full-rollback baseline is the correct choice over the original
surgical restore — it recovers the finish subsystem as an internally-consistent
unit instead of hand-reconstructing the deleted `climax_turn` / `parse_beats` /
`final_cut_context` helpers, and the archive tag makes it reversible. Issues
resolved during judgement:

1. **False-green gate (load-bearing).** The revert re-adds 564 lines of finish
   tests that build their own old-shape fixtures and use fixed-output mock LLMs;
   they pass against the reverted helpers while proving nothing about the live
   chapter-play doc. Phase 1 must therefore **not** be gated on a green suite, and
   Phase 2 must add a witness test driving the finish from a real chapter-play doc
   **first** (RED), then make it pass. AC amended accordingly. Without this, a
   green pytest would be a `plausible_wrong_answer`.
2. **"RED baseline" was imprecise.** Clarified: the honest RED is the *absence* of
   a chapter-shape finish test, not a red suite. Recorded in the Rollback note.
3. **Restore-then-delete churn.** The full revert restores `final_cut_turns` /
   `walkthrough` / `staging` only for Phase 2 to re-prune them. The cheaper
   cherry-pick path is noted; the user's explicit choice of a full, self-consistent
   rollback baseline stands. Documented as a decision, not a surprise.

Scope is minimal and internally consistent. Authority granted to enforce Phases
0–3; Phase 4 (LLM voice/continuity passes) remains a separate FR.

## Related

- FR-491 (`4040fac0`) — retired the finishes; this rolls Slice 4 back and carries
  the pruned capability forward into chapter scope.
- Tag `archive/dm-slice4-book-compose` (`04238f32`) — the pre-rollback
  book-compose implementation, recoverable for the Phase 4 voice pass.
- `examples/dungeon_master/api/turn_ops.py` — restored `final_cut_context`,
  `climax_turn`, `parse_beats` (re-scoped to `chapters.cards[cid].turns`).
- `examples/dungeon_master/api/chapter_ops.py` — `close_chapter` stores final text;
  new `compose_book_deterministic`.
- `examples/dungeon_master/prompts/final_cut.yaml` (restored via revert at
  `4040fac0^`) — the fidelity prompt, re-scoped per chapter.
- `examples/dungeon_master/book.yaml` / `prompts/book.yaml` — removed by the
  rollback; recovered from the archive tag as the Phase 4 revision pass.
- `docs/diary/diary-2026-06-16-the-capability-pruned-with-the-duplication.md` — the rationale.
- Scripture seed `verification_checkpoint_primitive` — Phase 4 driver.
