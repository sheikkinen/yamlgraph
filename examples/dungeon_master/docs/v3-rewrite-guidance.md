# Dungeon Master — Learnings from v2, Guidance for a v3 Rewrite

**Status:** Forward-looking design doctrine. Distilled 2026-06-21 from the FR-474 → FR-555
arc (the book-spine rewrite, the continuity program, and the 10025-BC → 10036-BC
calibration corpus).
**Audience:** whoever starts DM v3.
**Companion docs:** [`architecture.md`](architecture.md) (the v2 *how*),
[`continuity-issues.md`](continuity-issues.md) (the gap analysis),
[`continuity-projection-plan.md`](continuity-projection-plan.md) (the projection thesis),
[`refactoring-plan.md`](refactoring-plan.md) (the v2-shippable contract program),
[`plan-generative-plot-model.md`](plan-generative-plot-model.md) (the v3 plot-model target design).

> **The one-sentence thesis.** v2 proved that *turn-by-turn play produces excellent prose*
> and *a typed ledger can hold identity state* — but it reconstructs load-bearing plot
> facts **from the prose it just generated**, and it gates only **one** of its two
> authoring boundaries. v3 should keep the prose engine, **project** the load-bearing
> facts instead of reconstructing them, and **gate every boundary that authors structure**.

---

## 1. What v2 got right (keep these)

These are validated by the corpus; a v3 rewrite that drops them regresses.

1. **The deterministic-vs-generative seam split.** Hand the model assembled context and
   ask **only for prose/structure it cannot derive**; let pure code author everything that
   can be computed (beat resolution, phase, persistence, decay, retrieval). This is the
   single highest-leverage discipline in v2 — it makes the LLM's job small and the
   system's behaviour testable. Keep it as the governing law.

2. **The ledger as agent memory, not regenerated state.** The close emits a *delta*
   (`add`/`reaffirm`/`update`/`invalidate`); deterministic code applies it. **Zero ops
   carry the inherited set forward unchanged.** This killed the bond-reset and clan-flip
   classes outright. The principle generalizes: *the LLM authors meaning; deterministic
   code authors persistence.* Never let a generative step regenerate a whole state object
   it could silently shrink.

3. **Typed boundary normalization (`the_one_law`).** Validate external/LLM output into a
   typed shape at the boundary it enters, and **drop** ungrounded data there (a
   relationship lacking ≥2 named parties or a citation never enters the ledger). A bug
   killed at the boundary cannot manifest downstream.

4. **No silent fallback (Commandment 6).** Every "empty result" in v2 either raises or is
   an explicit, tested no-op. An empty LLM completion is treated as a content-policy
   decline and raised, never written over the draft. Preserve this — silent fallbacks are
   how a plausible-wrong-answer ships.

5. **Visibility-not-gate instruments.** The continuity *witnesses* (FR-522/538/542/554) are
   deterministic, roster-scoped, and **never raise** — they measure, they don't block.
   This let the team see drift without making the pipeline brittle. Keep a clear line
   between **instruments** (observe, never block) and **gates** (block at an authoring
   boundary). Confusing the two is how FR-521's advisory "feed-forward" was mistaken for a
   fix until a witness falsified it.

6. **Bounded-retry-then-raise enforcement.** The outline gates detect → re-invoke with a
   feedback correction block → bounded retry → raise. This is the right shape for any
   generative step with a deterministic acceptance test. Reuse it verbatim.

---

## 2. The central architectural mistake: reconstruction over projection

**The defect class that survived every v2 wave is reconstruction.** v2 authors an outline
up front, but **lifecycle and world state are inferred from the prose at chapter close**.
Every `character_lifecycle` entry's `source_chapter` equals the chapter it was *extracted
from* — there is no plot fact in v2 authored *ahead of* the prose that realizes it. An
inference over the generator's own output can lie, and it did (the Witta ch7→ch8
resurrection, the Arnulf early reveal).

**The litmus test (borrow it for v3): parallel-safety.** A fact is *truly projected* iff
two chapters' prose could be generated **without one reading the other's prose**. v2 *must*
serialize chapters because each waits to read the previous chapter's prose-derived state —
that forced ordering is the architectural symptom of reconstruction. If a fact must be read
back out of prose, it is not projected.

**v3 direction:** keep the turn engine; change the *direction of truth* for the small set
of facts that cause reader-visible breaks — **lifecycle (alive/dead/return floor) and
resolved-conflict identity.** Author them up front as a write-once, monotonic ledger;
**project** the chapter cast and the prose-exclusion set from it; **generate prose from the
ledger**, then validate a proposed *delta* against the prose rather than re-deriving state
from scratch.

> **Critical nuance (FR-533 §6, hard-won).** "Validate the prose, then record what it says"
> is **inverted for plan-protected characters**. When the synopsis needs a character alive
> for the rest of the arc, a prose death is the *error to prevent*, not the *truth to
> record*. v2 already enforced plan-over-prose **precedence for bookkeeping**
> (`lifecycle_resolver`, `chapter_memory > live_synopsis > seam_packet`) but never fed it to
> **generation** — so the turn engine could narrate a death the ledger then refused to log.
> **v3 must push plan-over-prose all the way to prose-generation time**: feed the
> protected-character set and any authored reappearance floor into the turn director *and*
> the final cut, so a plan-protected character can never be killed (or revived early) on the
> page. Then there is no conflict for any gate or extractor to reconcile.

---

## 3. The gate lesson: guard every authoring boundary, not every detector

The sharpest v2 process bug (FR-555): a gate guards a **detector at a boundary**, but v2
has **two** chapter-authoring boundaries and gated only one.

- The initial partition (`outline_chapters`) is gated by `reversal_pack_gap`,
  `unplayable_beat_gap`, `composition_gap`.
- The FR-523 state-aware **reoutline** (`reoutline_chapter_beats`) re-authors a chapter's
  beats from the full synopsis after each close — and committed them validating **only**
  non-emptiness. The exact defect `reversal_pack_gap` exists to prevent re-entered through
  this ungated second boundary (the 10036-BC Arnulf double-return). Running the existing
  detector on the committed card returns the violation — the detector was right; it was
  never wired in.

**v3 rules:**
1. **Enumerate authoring boundaries explicitly.** Any step that writes `beats`, `cast`,
   `summary`, lifecycle, or relationships is an authoring boundary. Make the list a
   first-class artifact, not an emergent property of the call graph.
2. **A detector that earns a gate is applied at *every* boundary that can produce its
   target artifact.** Bind the gate to the artifact, not to one call site.
3. **No recorded constraint may be a dead letter.** `allowed_reappearance_from_chapter` was
   carried in every seam packet and enforced on **no** prose generator. If a field exists,
   a deterministic step must consult it, or it should not exist. (Audit: for each typed
   field, name the code that reads it as a constraint. Unread fields are removed or wired.)

---

## 4. Typed lanes: the continuity ceiling is a missing-lane problem

v2's continuity is **strong exactly where a fact has a typed lane** (lifecycle, faction,
relationships) and **weak exactly where it does not** (physical/positional micro-state:
rope configuration, who is above/below, prop possession, climb phase). The bulk of the
residual 10025-BC complaints are in the untracked lane — the model improvises physical
state every turn with no ledger to contradict it, and the cross-seam reviewer catches the
drift the pipeline cannot see.

**v3 direction:** treat "does this fact class have a typed lane?" as a design checklist, not
an afterthought. For each class of fact the reviewer complains about, either (a) give it a
typed lane with deterministic carry-forward, decay, and retrieval (as relationships got in
FR-513–518), or (b) explicitly declare it out of scope and stop pretending the prose holds
it. The positional/prop lane is the single biggest structural gap; it likely needs
*turn-grain* state (not the chapter-grain ledger v2 has).

---

## 5. The witness/reviewer split is the routing signal, not a redundancy

v2 ended with two continuity assessors that disagree by construction:

- **Deterministic witnesses** read the **committed ledger** — precise, roster-scoped, never
  raise, but blind to anything not in a typed lane.
- The **LLM `book_reviewer`** reads the **prose** — sees everything a reader sees, including
  the untyped lanes, but is non-deterministic and cannot gate CI.

Their **disagreement is information**: a break the witness sees but the reviewer doesn't is
a false positive to tighten; a break the reviewer sees but every witness misses is a
**fact class with no typed lane** (the v3 backlog of what to promote next). v3 should make
this routing explicit — a break is either *ledger-visible* (deterministically gateable) or
*prose-only* (needs a typed lane before it can be gated). Don't try to make the reviewer a
gate; use it as the discovery instrument for the next lane to build.

---

## 6. The capped scene is a hard constraint that must shape the outline

A chapter plays under a fixed turn cap (FR-501) and closes only when the director computes
`scene_complete = (k == n)` over its finite beats. Two whole defect classes (the phantom
reversal, the unplayable time-skip epilogue) are *consequences of authoring beats the
capped scene cannot enact*. v2's cure was right: **catch un-enactable structure at the
outliner, never downstream** — because the only "scene is over" signal at the play boundary
is the very thing the defect suppresses. v3: make "can the capped scene physically enact
this beat?" an outline-time acceptance test for every beat, at every authoring boundary
(see §3).

---

## 7. Process learnings (the doctrine that paid off)

- **The upstream march.** Each continuity wave pushed the residual defect one boundary
  earlier (turn → close → open → outliner → synopsis). *Where a symptom can be measured is
  rarely where it can be fixed.* Expect v3's hard bugs to live upstream of where they show.
- **Investigation before fix.** When a bug needs >15 min to write the failing test, split
  into an investigation FR (build the harness proving the causal chain) then a fix FR. The
  10036-BC root cause was nailed by running the *existing* detector against the *committed*
  artifact — the proof was a one-liner once the harness existed.
- **Falsify the mass/context hypotheses early.** FR-553 falsified "the small model is
  drowning in a 12k prompt" (facts were present-but-ignored, not missing). Before adding
  context (codices, bigger prompts), prove the fact is absent — often it is present and the
  lever is salience or a constraint, not mass. (FR-548's world-codex was rolled back for
  exactly this reason: it authored prose from the synopsis *before* action, leaking
  non-roster names — a placement defect a content filter would only have masked.)
- **A demo proves the abstraction is worth having; a test proves a constraint holds.** Keep
  the live single-chapter replay (FR-522) as an *instrument* and the unit tests as *wiring
  proofs* — and never confuse the two for efficacy evidence.

---

## 8. A concrete v3 target shape

```
synopsis ──▶ cast ──▶ outline (title/summary/beats/cast/entry_state/exit_state)
                          │
                          ▼
        ┌──────── AUTHORED ONCE, WRITE-ONCE, MONOTONIC ────────┐
        │  LIFECYCLE LEDGER: per character existence timeline   │
        │  + reappearance floor;  per conflict resolved-at id   │
        └───────────────────────────┬───────────────────────────┘
                                     │  (projected, not inferred)
   per chapter, in order  ──────────┤
                                     ▼
   running_scene  ◀── PROJECTS cast = ledger.alive_at(ch);
        │              excluded   = ledger.not_yet_returnable(ch);
        │              protected  = ledger.plan_protected(ch)   ── fed to BOTH
        ▼                                                          director + final cut
   turns (map ▶ director ▶ recap)   [keep v2's engine verbatim]
        │
        ▼
   chapter_close ── proposes a lifecycle DELTA
        │
        ▼
   JUDGE ▶ AMEND  ── validate delta vs prose AND ledger:
        │             • prose death of a protected char ⇒ reject the PROSE (regenerate)
        │             • prose death of a mortal char    ⇒ accept the delta
        │             • once dead, may only advance a reappearance floor (never flip alive)
        ▼
   COMMIT (write-once)

   ENFORCEMENT (every authoring boundary, §3):
     outline AND reoutline ─▶ reversal_pack_gap · unplayable_beat_gap · composition_gap
                              · reappearance-floor check · entry/exit compose check
```

**Acceptance litmus for v3:** the lifecycle ledger is truly projected iff two chapters'
prose could, in principle, be generated against it **without one reading the other's
prose**. If a chapter still needs the prior chapter's *prose* (not its authored ledger
delta) to know who is alive and where, the fact is still reconstructed — and the same class
of breaks will return.

---

## 9. Anti-patterns to retire in v3

| v2 anti-pattern | v3 replacement |
|---|---|
| Lifecycle/world state **reconstructed from prose** at close | Authored up front, **projected**; close proposes a validated delta |
| Plan-over-prose enforced for **bookkeeping only** | Plan-over-prose fed to **prose generation** (protected set → director + final cut) |
| A detector gated at **one** authoring boundary | Gate bound to the **artifact**, applied at **every** boundary that writes it |
| Typed fields that **no code reads as a constraint** (dead-letter floor) | Every field has a named deterministic consumer, or it is removed |
| Fact classes with **no typed lane**, left to prose | A typed lane (carry-forward + decay + retrieval) or an explicit out-of-scope declaration |
| Adding **context/mass** to fix an ignored fact | Falsify absence first; reach for **salience/constraint** before mass |
| Confusing the **reviewer** (prose, non-deterministic) with a **gate** | Reviewer is the discovery instrument for the next lane; gates are deterministic |
