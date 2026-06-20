# Feature Request: DM v2 — World Bible (Ground-Truth Input or Post-Action Grounding)

**Priority:** MEDIUM (length/depth lever — re-earns the FR-548 length goal from a sound source)
**Type:** Feature
**Status:** Approved with conditions (Option A; fold C1-C5; enforce after FR-551)
**Effort:** ~2 days
**Requested:** 2026-06-20

## Summary

Re-introduce faction/location **world texture** — the goal FR-548 aimed at — but from a *sound*
source instead of a plot synopsis. A **world bible** describes the standing world (geography,
factions, history) independent of this book's plot. Two leak-proof mechanisms are proposed; **pick
one by intent at Judgement**:
- **(A) Ingested premise input** — an authored `<premise>-world.txt` alongside the premise file,
  loaded as **ground truth** (constrains generation pre-action, zero hallucination by definition).
- **(B) Post-action grounding** — author backstory **from the chapters that actually appeared**
  (physically cannot invent characters or reverse facts; purely additive reflective texture).

Both fix the FR-548 placement defect by construction: the bible is either *ground-truth input* or
*post-action grounded*, never *speculative pre-action prose derived from plot*.

## Value Statement

The book regains the world-depth and length FR-548 chased (toward novelette range) without the
character-leak and plot-derived-faction hazards — because a world bible is sourced from authored
ground truth or from committed chapter text, neither of which can invent a `Reinmar` or a "combined
survivors" faction.

## Problem

FR-548 proved that **deriving a world bible from a plot synopsis is a category error** (see FR-550):
the synopsis *is* plot, so "factions" come out as plot groupings and characters leak into world
texture. But the underlying need is real and unmet:

- The generator has **no world-grounding stage** — faction identity (Aschenwulf vs Bärenschädel clan
  politics) and location lore (the flood zone, the ledge, the salt road) are invented inconsistently
  per chapter at 0.7 temperature.
- Empirically, the *calm, well-grounded* book scored best (10032-BC: 0 breaks, 5/5) and the
  *twist-dense* book worst (10031-BC: 8 breaks, 1/5). World texture adds the **calm kind of length**:
  standing-world depth, not new reversible events.

The lesson from FR-548 is **placement, not abandonment**: world texture must come from a source that
*cannot drift from the action*. That means ground-truth input (authored, fixed) or post-action
grounding (derived from what already happened) — never speculation ahead of the prose.

## Proposed Solution

> **Decision made at Judgement (2026-06-20): build Option A only.** Option A is leak-proof with zero
> LLM (cheapest sound path, reuses the FR-548 guarded-block invariant) and *constrains* the writing,
> which is the higher-value intent for a saga whose breaks come from inconsistent standing-world
> facts. **Option B (post-action appendix) is DEFERRED to a follow-up FR** — do not build it in v1
> (`Purge`: building both reproduces the two-masters confusion that sank FR-548). Option B is retained
> below for the follow-up's reference only.

### Option A — Ingested premise input (world as ground truth) — **CHOSEN (v1)**

The premise is already a file (`premises/floodmark-saga.txt`, read by `generate_and_review.sh`). Add
an **optional** sibling `premises/floodmark-saga.world.txt` — an authored world bible (factions,
locations, history). On generation:
- If present, load it into `doc["world_bible"]` verbatim (no LLM — it is ground truth).
- Thread it as a `{% if %}`-guarded grounding block into `chapter_outline.yaml` and `final_cut.yaml`,
  exactly where FR-548 wove the codex, governed by the existing "compose, do not invent" rule.
- Absent file → byte-identical prompts (the guarded-block invariant).

**Why leak-proof:** the bible is authored by a human, never generated, so it cannot hallucinate a
non-roster character or a plot-derived faction. It *constrains* generation rather than competing with
it. Any character it names is the author's responsibility to also place in the premise/roster.

### Option B — Post-action grounding (world from committed chapters) — **DEFERRED (follow-up FR)**

> Not built in v1 (Judgement C4). Retained for the follow-up's reference. Anchor verified:
> `compose_book_deterministic(doc)` exists at [chapter_ops.py L366](examples/dungeon_master/api/chapter_ops.py#L366)
> ("FR-492 Phase 3"), and `world_state.py` (the ledger it would read) exists — both confirmed present
> for when the follow-up is taken up.

After all chapters are played and closed (the action exists and is committed), run a
`world_bible.yaml` stage over the **final chapter texts + world_state ledger** (not the synopsis) to
author faction/location backstory *for the factions and places that actually appeared*. Persist as
`doc["world_bible"]` and append as a reflective **appendix/codex section** in the deterministic Book
compose (FR-492 Phase 3), after the narrative.

**Why leak-proof:** the stage reads committed text, so it physically cannot invent `Reinmar` (he is
not in the chapters unless he was written) or flip the weapon state (it summarizes, never narrates).
A post-action appendix *cannot contradict the action it summarizes* — additive by construction.

### Shared constraints (apply to the chosen Option A)

- **No character invention (C2 — the gate).** The bible names factions and locations; any person it
  references must already exist in the roster (main or supporting tier, FR-551). A boundary check
  warns/drops a bible entry that names a non-roster person — the FR-548 leak made impossible
  structurally. **This requires FR-551's supporting tier (C1 dependency); enforce FR-552 after FR-551.**
- **No plot-derived factions.** Stable institutions only (Aschenwulf, Bärenschädel valid; "Wenda's
  people", "the combined survivors" rejected). For Option A this is the author's discipline, backed by
  the no-character-leak boundary check.

## Acceptance Criteria

- [x] **Judgement records the (A)/(B) decision** with rationale — **Option A chosen** (see Judgement
      2026-06-20); Option B deferred to a follow-up FR (`spec_kill` — the cheapest bug is the one
      killed in the spec).
- [ ] **(C1 — dependency) Enforce after FR-551.** The no-character-leak check reconciles against
      `roster ∪ supporting`; FR-551's tracked supporting tier must exist first.
- [ ] **(C3 — deterministic RED, the gate)** committed separately, `SKIP=pytest`, **Option A only:**
      loading a present `*.world.txt` populates `doc["world_bible"]` verbatim; absence leaves
      `chapter_outline`/`final_cut` prompts byte-identical (guarded-block invariant).
- [ ] **(C2 — deterministic RED, the gate) No-character-leak invariant:** a `world_bible` entry naming
      a non-roster person is warned/dropped at the boundary (`the_one_law` — normalize where the
      authored file enters); every person it names resolves to a roster member (main or supporting
      tier). The explicit mechanical guard against the FR-548 defect — the prompt alone does not hold
      (`gate_checks_shape_not_substance`).
- [ ] The Option-A loader + guarded blocks lint clean; threaded into `chapter_outline.yaml` /
      `final_cut.yaml` via `{% if %}`-guarded blocks so absence is byte-identical.
- [ ] **(C4 — scope freeze) Option A only.** NO `world_bible.yaml` LLM stage, NO post-action grounding,
      NO `compose_book_deterministic` appendix in this FR. Purge any Option-B artifact from the v1
      build.
- [ ] **(C5 — visibility evidence, NOT a blocking test)** `demo-output.log` records the added words
      and the continuity score vs the 10032-BC baseline, documenting the additive claim from a clean
      source. Never a CI gate (LLM-nondeterministic).
- [ ] Example-exempt: NO `@pytest.mark.req`, NO capability YAML; changelog fragment `type: feat`,
      `scope: examples`, no `req:`.
- [ ] Distill diary entry (the placement principle: ground-truth input or post-action grounded, never
      pre-action speculation).
- [ ] New modules/prompts under the 450-line ceiling.

## Alternatives Considered

- **Re-derive from the synopsis (FR-548's approach)**: rejected — proven category error (FR-550); the
  synopsis is plot, so the bible inherits plot's characters and groupings.
- **Build both (A) and (B) in v1**: rejected — they serve different intents (constrain vs decorate);
  shipping both reproduces the two-masters confusion that sank FR-548. Pick one; the other is a
  follow-up if the first proves its worth.
- **Mutable world bible (factions evolve per chapter)**: rejected — faction *stance* evolution belongs
  to the relationship ledger (FR-545), not the bible. The bible is immutable standing-world reference
  (option A) or a once-authored post-action appendix (option B).
- **Skip the no-character-leak boundary check, trust the prompt**: rejected — `gate_checks_shape_not_substance`;
  the FR-548 leak proves the prompt alone does not hold. The roster-reconciliation check is the
  mechanical guard, depending on FR-551's tracked supporting tier.

## Related

- `feature-requests/FR-548-dm-v2-world-codex-backstory-stage.md` — the failed synopsis-derived approach
- `feature-requests/FR-550-dm-v2-rollback-world-codex.md` — removes FR-548 first; this re-earns its goal soundly
- `feature-requests/FR-551-dm-v2-supporting-cast-tier.md` — provides the tracked roster the leak-check reconciles against (dependency)
- `examples/dungeon_master/scripts/generate_and_review.sh` — premise-file loader (option A entry point)
- `examples/dungeon_master/prompts/final_cut.yaml` / `chapter_outline.yaml` — guarded grounding-block consumers
- FR-492 Phase 3 deterministic Book compose — option B appendix insertion point
- Evidence: 10032-BC (grounded, 0 breaks, 5/5) vs 10031-BC (twist-dense, 8 breaks, 1/5) — world texture adds the calm kind of length

## Judgement (2026-06-20) — APPROVE WITH CONDITIONS (decision: Option A)

**Verdict: APPROVE WITH CONDITIONS.** The need is real and the placement principle (ground-truth input
or post-action grounded, never pre-action speculation) is the correct lesson from FR-548. The FR
rightly demands the (A)/(B) choice be made at Judgement (`spec_kill`) — so I make it.

**Decision: build Option A (ingested premise input) for v1.** Rationale:
- **Leak-proof by construction with zero LLM.** A human-authored `*.world.txt` loaded verbatim cannot
  hallucinate a non-roster `Reinmar` or a plot-derived "combined survivors" faction. Option B still
  runs an LLM authoring step (lower leak risk than synopsis-derived, but not zero) and adds
  idempotency + committed-text-reading complexity.
- **Cheapest sound path.** The premise is already a file read by `generate_and_review.sh`; an optional
  sibling file + a `{% if %}`-guarded grounding block into `chapter_outline.yaml`/`final_cut.yaml`
  reuses the exact byte-identical-absence invariant FR-548 already proved. Lowest new surface.
- **It constrains rather than competes.** Option A shapes the writing (world -> book); that is the
  higher-value intent for a survival saga whose breaks come from inconsistent standing-world facts
  (10031-BC). Option B (book -> world appendix) decorates after the fact and is the correct **follow-up**
  once A proves its worth — explicitly deferred, not built in v1 (avoids the two-masters confusion that
  sank FR-548).

**Insertion points verified:** `compose_book_deterministic(doc)` exists at `chapter_ops.py` L366
("FR-492 Phase 3") — that is the real Option-B appendix anchor **for the deferred follow-up**; not
needed for A. `generate_and_review.sh` premise loading is the A entry point. `world_state.py` exists
(the ledger B would read) — confirmed, follow-up only.

**Conditions (blocking — for the Option-A build):**
- **C1 — Dependency on FR-551 is hard.** The no-character-leak boundary check (every person named in
  `world_bible` resolves to a roster member) requires FR-551's tracked supporting tier to exist; a
  guide named in the bible must reconcile against `roster ∪ supporting`. Enforce FR-552 **after**
  FR-551. Until then the leak-check can only reconcile against the main roster and would false-warn on
  legitimate supporting NPCs.
- **C2 — The no-character-leak invariant is the gate, as a deterministic RED.** A `world_bible` entry
  naming a non-roster person is warned/dropped at the boundary (`the_one_law` — normalize where the
  authored file enters). This is the explicit mechanical guard against the FR-548 defect; the prompt
  alone does not hold (`gate_checks_shape_not_substance`).
- **C3 — Guarded-block byte-identical-absence RED.** Absent `*.world.txt` leaves `chapter_outline`
  and `final_cut` prompts byte-identical (the FR-548 guard pattern, reused). Deterministic.
- **C4 — Scope-freeze: Option A only.** No `world_bible.yaml` stage, no post-action grounding, no
  `compose_book_deterministic` appendix in this FR. Those are the deferred Option-B follow-up. Purge
  any Option-B artifact from the v1 build (`Purge` doctrine).
- **C5 — Length/continuity stays visibility-only.** The added-words + score-vs-10032-BC claim is
  demo-log evidence, never a CI gate (LLM-nondeterministic).

**Ordering:** FR-550 -> FR-551 -> FR-552. With Option A frozen and C1-C5 folded, no re-judge required.
Status -> **Approved with conditions (Option A; fold C1-C5; enforce after FR-551).**
