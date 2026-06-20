# Feature Request: DM v2 Identity / Allegiance-Reset Continuity Witness

**Priority:** MEDIUM (covers the *pairwise named-edge* allegiance slice only; role/collective resets -- the majority of the cited breaks -- are a separate follow-up, see Scope boundary)
**Type:** Enhancement
**Status:** Enforced (RED 4c561f77, GREEN this commit) -- ledger witness live, chapter_close tightened. C1-C4 folded; baseline corrected to transition_count==0 (total fidelity gap, measured).
**Effort:** ~1 day
**Requested:** 2026-06-20

## Summary

Make the **relationship memory ledger** (`world_state.relationships`) the system of record for
allegiance over time, and read it for resets. The ledger already models allegiance correctly --
type-independent edge identity, `update`/`invalidate` delta ops, bi-temporal `valid_from/to`,
and a recap-citation grounding gate -- and `chapter_close.yaml` already instructs the writer to
emit an `update` when a bond's type turns (e.g. `enmity->romantic_bond`). The verified defect is
not a missing data model: it is **fidelity** -- the writer fails to emit those ops, so the ledger
sits static while the prose flips. This FR (a) adds a **deterministic ledger-fidelity witness**
that reports recorded allegiance transitions and surfaces a static ledger as the diagnostic, then
(b) tightens `chapter_close` so the writer reliably commits allegiance changes, validated by the
witness. Visibility-not-gate posture (FR-522/530), consistent with `seam_entrance` (FR-538) and
`fact_reversal` (FR-542). Scope is the **named pairwise edges** the ledger can model; character-
grain authority/role resets and collective (group) allegiance are explicitly carved out.

**Coverage honesty (C1).** After that carve, this FR addresses only the *pairwise* slice of the
cited breaks -- roughly the Hilde/Gunnar bond, ~1 of the 7 identity/allegiance breaks in 10031-BC.
The role resets (Ylva, Reinmar) and the collective allegiance (Gunnar vs the Baerenschaedel
*group*) have no pairwise edge to diff and remain the LLM reviewer's domain / a named follow-up.
The headline "7 of 8" justifies the *rail*, not this mechanism's reach.

## Value Statement

The relationship ledger becomes a faithful, machine-readable record of who is allied/bonded/
opposed to whom across the book -- so allegiance is *documented* where it belongs (the memory
ledger), and a per-run witness reports every recorded transition plus a fidelity gauge
(transitions recorded vs. prose flips the reviewer sees). The largest continuity-debt rail stops
being invisible to the deterministic layer and is measured against a moving number.

**Limitation (C4).** The witness counts *grounded op-emission*, not *break correctness*: it cannot
distinguish a correct recorded transition from a hallucinated-but-grounded one, and it does **not**
localize the *unrecorded* flips (the actual defect) to a seam. On a 7-break book it will read ~1.
It is a regression gauge for Part 2 and a complement to the LLM reviewer's localization -- never an
all-clear when the number is low (`plausible_wrong_answer` guard).

> **Evidence (4 books on the floodmark-saga premise).** The LLM reviewer flags this class on
> every book, and the deterministic witnesses are structurally blind to all of it:
>
> | Book | reviewer breaks | seam_entrance | fact_reversal | breaks on the identity/allegiance rail |
> |------|-----------------|---------------|---------------|----------------------------------------|
> | 10028-BC | 5 | 0 | n/a | several |
> | 10029-BC | 3 | 0 | n/a | several |
> | 10030-BC | 2 | 0 (false-clear, → FR-543) | 0 | 1 (Hilde/Gunnar) |
> | 10031-BC | 8 | **1** (Reinmar, post-FR-543) | 0 | **7 of 8** |
>
> In 10031-BC, **7 of 8** reviewer breaks are pure identity/allegiance resets: "Gunnar stands
> WITH Hilde against the Bärenschädel leaders (Ch4)… in Chapter 5 moves closer to the
> Bärenschädel leaders and positions the shield in front of them — a silent flip with no
> in-story transition"; "Ylva [is] the central authority figure (Ch5)… in Chapter 6 she
> becomes a supporting figure… reactive and physically subordinate"; "Reinmar… one voice among
> four, repeatedly overruled (Ch5)… in Chapter 6 he becomes the primary authority figure whose
> route everyone follows." Every one of these is a relationship/allegiance/authority reversal,
> not an entrance, a lethal exit, a fact reversal, or a dead-character appearance.

## Problem

The continuity-witness layer covers **world-grain** state (objects, facts, lifecycle) and
**entrances/exits**, but nothing covers **character-grain relational state over time**:
*who is allied with whom, who commands whom, what bond exists between two characters, and
whether that flips without a bridge.*

The data to measure it **already exists** and nothing reads it for reversal detection:

- `world_state.relationships` (`Relationship`, [world_state.py](examples/dungeon_master/api/world_state.py) L45) is explicit, bi-temporal ledger state: `between`, `type`, `status`, `tensions`, `valid_from`, `valid_to`, `last_reaffirmed`. It exists precisely because relationships used to reset at every chapter break ("lovers re-met as strangers", FR-513) — but no detector compares an edge's `status`/`type` across the seam, and **the writer rarely records the change in the first place** (verified below).
- `chapter_memory.character_state_deltas` (folded by `lifecycle_resolver._state_map_from_memory`) records `{name, from_state, to_state, evidence}` per chapter — but in real output it carries only lifecycle deltas (`Arnulf -> missing_presumed_dead`), never allegiance/role transitions.

**Verified against `10031-BC/story/story.json` (the book with 7/8 breaks on this rail):**

- Relationship edges are **static across every flagged seam**. Hilde/Gunnar is `romantic_bond` /
  `active` Ch2->Ch8; Hilde/Reinmar `alliance` / `active` and Gunnar/Reinmar `enmity` / `active`
  are constant Ch4->Ch8. **No `update`/`invalidate` op fired** at the Gunnar flip (Ch4->Ch5) or
  anywhere the reviewer saw a reset. The ledger is self-consistent; the prose is not.
- `character_state_deltas` records **only** `Arnulf -> missing_presumed_dead` every chapter;
  **Ch5 has zero deltas**. No allegiance/authority delta exists for Gunnar, Ylva, or Reinmar.

So the root cause is **ledger-prose desync via missing writes**, not a missing detector: the
writer performs the flip in prose but never commits the `update` op the ledger is designed to
receive. A detector that only *reads* the ledger therefore measures ledger self-consistency (a
property the writer already maintains), not prose fidelity (where the defect lives) -- which is
exactly why the first cut of this FR was rejected (see Judgement). The fix must make the writer
record the change, then read the now-faithful ledger.

(Note: `character_overlay.derive_overlay` (FR-541) *is* wired into the turn loop and consumed by
`character_intent.yaml`; it is simply not persisted. It is character-grain scalar state and the
wrong grain for pairwise allegiance -- see FR-544 for persisting its trail.)

The existing detectors are adjacent but do not cover it:
- `seam_entrance_gap` (FR-538): a character *appears* unbridged — presence, not allegiance.
- `fact_reversal_gap` (FR-542): a *world fact* flips (secured → unclaimed) — not a *relationship/role*.
- `prose_continuity.detect_dead_character_prose_violations` (FR-510): a *dead* character acts — a lifecycle status, not a relational reset.

## Proposed Solution

Use the **relationship memory ledger** as the system of record, in two parts. Part 1 (the
deterministic, this-FR core) is a **ledger-fidelity witness** that reads the ledger and measures
whether allegiance changes are being recorded. Part 2 (a small, bounded prompt change validated
by the witness) makes the writer actually record them. Ordering follows measure-first
(FR-371 → FR-372): build the gauge, prove the ledger is static under a book the reviewer says is
full of flips, then close the fidelity gap and watch the gauge move.

### Part 1 — Ledger-fidelity witness (deterministic, no LLM)

A new leaf `examples/dungeon_master/api/allegiance_ledger.py`:

```python
def allegiance_transitions(doc: dict) -> dict:
    """Recorded allegiance transitions over the whole book, read from the ledger.

    Reads the FINAL chapter's committed `world_state.relationships` -- which carries
    the entire bi-temporal history (closed edges are never dropped unless ungrounded,
    world_state.py L310). A transition is a pair (`_rel_key` identity, participant-set,
    type-independent) with a CLOSED edge stamped `valid_to == K` and a NEW current edge
    stamped `valid_from == K`; K localizes the transition to a chapter. No adjacent-
    snapshot walk, no multi-edge ambiguity.
    Returns {"transition_count", "ungrounded_count", "by_pair": [
        {"between": [a, b], "from": ..., "to": ..., "at_chapter": K, "grounded": bool}
    ], "posture": "visibility-not-gate"}.
    """
```

Mechanics (mirroring `fact_reversal` discipline — frozen sets, `_rel_key`, `_norm_name`, no LLM):

1. **Recorded transitions (C2: read the stamps).** From the final committed
   `world_state.relationships`, group edges by the type-independent **`_rel_key`**. A pair with a
   closed edge (`valid_to == K`) and a new current edge (`valid_from == K`) is a transition at
   chapter K; read `from = closed.type`, `to = current.type`. A change that crosses a **frozen
   antonym set** (`enmity ↔ alliance`, `romantic_bond ↔ estranged`, `command ↔ subordinate`) is
   reported with its `recap_citations` grounding flag. This needs ONE ledger, not N snapshots.
2. **Grounding / fidelity signal.** A transition carrying a `recap_citation` is a *recorded,
   evidenced* change → reported for review (visibility). A transition with **no** citation, or an
   edge closed (`valid_to` set / `status` ∈ `{dormant, archived}`) without evidence, increments
   `ungrounded_count`. The headline diagnostic is **fidelity**: when `transition_count` is ~0
   across a book the reviewer flags for many allegiance breaks, the witness is *proving the writer
   isn't recording them* — that static number is the actionable signal, not a false all-clear.

Frozen antonym sets only (no widening — `regex_fourth_exclusion`). `transition_count` /
`ungrounded_count` are witness numbers; nothing raises. Emit an `allegiance_transitions` block
from [emit_continuity_witness.py](examples/dungeon_master/scripts/emit_continuity_witness.py),
alongside `seam_entrance` and `fact_reversal`:

```json
"allegiance_transitions": {
  "transition_count": 1,
  "ungrounded_count": 0,
  "by_pair": [{"between": ["hilde", "gunnar"], "from": "enmity", "to": "romantic_bond", "at_chapter": "2", "grounded": true}],
  "posture": "visibility-not-gate"
}
```

### Part 2 — Ledger fidelity (generative; close the desync)

`chapter_close.yaml` already instructs the writer to emit `update`/`invalidate` ops, but only
illustrates *type* turns (`enmity → romantic_bond`). Verified output shows the writer omits the
op for **cooling** and **stance flips**. Tighten the relationship-delta instruction to require an
op whenever a tracked pair's *stance* changes this chapter — explicitly covering
`romantic_bond → estranged` (a bond cooling) and `alliance ↔ enmity` (a side switch), grounded in
a specific recap quote (the existing grounding gate still drops ungrounded ops). The witness from
Part 1 is the regression measure: after the change, re-running 10031-BC should raise
`transition_count` from ~0 toward the prose's actual flips.

### Scope boundary (the honest carve)

The ledger models **named pairwise edges only**. Two sub-classes of the 10031-BC breaks are out
of scope for the ledger approach and must **not** be forced into it:

- **Character-grain authority/role resets** (Ylva central → subordinate; Reinmar overruled →
  obeyed leader): a single character's *role*, not a pairwise bond — no edge to diff.
- **Collective allegiance** (Gunnar vs the Bärenschädel leaders *as a group*): the group is not a
  roster name; `between` requires named participants.

These remain the LLM reviewer's domain (a character-grain role witness is a separate proposal).
The ledger path covers the **pairwise** resets (Hilde/Gunnar bond cooling Ch2→Ch3) and, via
Part 2, makes the writer record them — the durable fix that *documents allegiance over time in
the memory ledger*, which is where it belongs.

## Acceptance Criteria

- [ ] **(C2)** RED test (committed separately, `SKIP=pytest`) over a fixture whose final committed
      ledger holds, for one pair, a CLOSED edge (`valid_to == K`) crossing a frozen antonym into a
      NEW current edge (`valid_from == K`) **with** a `recap_citation` -> one `grounded` transition
      at chapter K; the same crossing **without** a citation -> `ungrounded_count == 1`.
- [ ] **(C2)** `allegiance_transitions` reads `valid_from`/`valid_to` stamps from the final
      committed `world_state.relationships`, grouped by the type-independent `_rel_key`; restricted
      to roster pairs and frozen antonym sets. No adjacent-snapshot walk.
- [ ] Fidelity gauge proven (measured against real data): the **final committed** 10031-BC ledger
      (Ch8) holds 3 edges, **all `valid_to=None`** -- NO closed edge anywhere -- so under C2 the
      witness reads **`transition_count == 0`**: the writer recorded *zero* bi-temporal allegiance
      transitions despite the reviewer's 7 prose flips. A committed synthetic fixture mirroring
      that all-current shape pins `transition_count == 0` (the real file is gitignored under
      `outputs/`). This total-gap reading is the headline diagnostic, not a near-miss.
- [ ] First chapter / no prior committed edge -> empty (additive, no false positives).
- [ ] **(C3)** Part 2 acceptance is a deterministic **prompt-content** assertion only: a test
      asserts `chapter_close.yaml` instructs an `update`/`invalidate` op for stance changes
      (cooling, side switch), not only type turns, with the grounding gate unchanged. Writer
      *compliance* is a hope, not a gate -- **no** AC asserts a regenerated book's transition_count
      rises (that is LLM-dependent; the witness is the ongoing gauge, not a pass/fail).
- [ ] `emit_continuity_witness.py` emits the `allegiance_transitions` block.
- [ ] **(C4)** Witness limitation documented in-module: counts grounded op-emission, not break
      correctness; no per-seam localization of *unrecorded* flips; a low count is not an all-clear.
- [ ] New leaf stays a leaf (imports `world_state`; imported by nothing in the seam-gate layer)
      and under the 450-line ceiling.
- [ ] Changelog fragment (`type: feat`, `scope: examples`, no `req:` — example-exempt).
- [ ] Distill diary entry.

## Alternatives Considered

- **Pure ledger-reading detector, no prompt change** (the rejected first cut): reading
  `world_state.relationships` for reversals measures ledger self-consistency, which the writer
  already maintains — so it scores 0 on every prose flip and would false-positive on the one
  legitimately recorded transition (Hilde/Gunnar Ch1→Ch2). The witness is kept *only* as a
  fidelity gauge whose static reading is the signal, and is paired with the Part 2 prompt fix
  that gives it something true to read.
- **Wire `derive_overlay` into turn context as the allegiance source**: rejected as
  `false_duplicate` — the overlay is *character-grain scalar* state (already wired, FR-541), the
  wrong grain for a *pairwise* bond. Allegiance lives in the `Relationship` edge
  (`between`/`type`/`status`/`valid_to`). Persisting the overlay's own trail is FR-544.
- **Widen `fact_reversal` to cover relationships**: rejected — relationships are character-grain
  bi-temporal edges with their own ledger (`valid_from/to`, `last_reaffirmed`); folding them into
  the world-fact antonym set would conflate two boundaries (`false_duplicate`).

## Related

- `examples/dungeon_master/api/world_state.py` — `Relationship` model (L45), `_INACTIVE_STATUSES`, `DECAY_AFTER`
- `examples/dungeon_master/api/lifecycle_resolver.py` — `_state_map_from_memory`, `_norm_name`
- `examples/dungeon_master/api/character_overlay.py` — FR-541 `derive_overlay` (wired but character-grain scalar; wrong grain for pairwise allegiance — see FR-544 to persist its trail)
- `examples/dungeon_master/api/fact_reversal.py` — FR-542 sibling detector (pattern to mirror)
- `feature-requests/FR-538-dm-v2-seam-entrance-witness.md`, `FR-542-dm-v2-seam-fact-reversal-gate.md`
- Evidence: `outputs/dungeon-master/10031-BC/review.md` (7 of 8 breaks), `continuity_witness.json`

## Judgement (2026-06-20) — REJECTED as specified; return to Plan

**The pain is real (Red Hat: approved).** The evidence table holds: identity/allegiance/authority
resets are the dominant reviewer-flagged break class, and no deterministic witness covers them.
Building a measure for this rail is worth doing.

**But the proposed mechanism reads the wrong layer — verified against the cited book, it would
score ZERO on the very breaks it is justified by.** I inspected `10031-BC/story/story.json`
directly:

- `world_state.relationships` edges are **stable across every flagged seam**. Hilde/Gunnar is
  `romantic_bond` / `active` from Ch2 through Ch8; Hilde/Reinmar `alliance` / `active` and
  Gunnar/Reinmar `enmity` / `active` are constant Ch4→Ch8. There is **no edge whose
  `type`/`status` flips** at the Ch4→Ch5 Gunnar seam, the Ch5→Ch6 Ylva seam, or the Reinmar
  seam. The detector's primary mechanic ("compare an edge's status/type across the seam") has
  **nothing to compare** — it returns `gap_count == 0` on the book the FR says has 7/8 breaks
  on this rail.
- `character_state_deltas` records **only** `Arnulf → missing_presumed_dead`, the same delta
  every chapter; **Ch5 carries zero deltas**, and there is **no** allegiance/authority/role delta
  for Gunnar, Ylva, or Reinmar anywhere. The secondary mechanic ("authority reversal over
  `_state_map_from_memory`") has **no input** for any cited break.

**Root cause of the misfire: the breaks live in the PROSE; the structured ledger stays put.**
This is the inverse of the FR-543 class. There, structured presence was fine and the prose was
unbridged. Here the structured relationship ledger is **self-consistent** (stable edges) while
the **prose** silently flips allegiance. A detector that reads the ledger measures *ledger
self-consistency* — a property the writer already maintains — not *prose-vs-ledger fidelity*,
which is where the defect lives. The same structural blindness FR-538/543 just fought, but this
time **unfixable by reading the ledger at all.**

**It would also FALSE-POSITIVE.** The one real ledger transition in the data — Hilde/Gunnar
`enmity` (Ch1) → `romantic_bond` (Ch2) — has no bridging `character_state_delta` (Ch2's only
delta is Arnulf). The proposed rule would flag it as an unbridged allegiance reset, yet the
reviewer did **not** flag it: it is a narrated enemies-to-lovers turn the prose bridges. So the
detector would simultaneously miss every true break and fire on a legitimate arc — the worst of
both error classes (`plausible_wrong_answer`).

**The deeper finding (graduate this): a deterministic witness must read the same layer the defect
is written in.** `fact_reversal` works because facts are committed structured state AND the prose
echoes them. Allegiance breaks are prose-only here; the relationship ledger does not capture them.
Reading structured state to catch a prose defect is a layer-mismatch.

**Paths back to Plan (pick the layer that contains the breaks):**

1. **Prose-grain detector (recommended, mirrors `fact_reversal`'s real strength).** Apply the
   frozen-antonym discipline to the **chapter text**, not the ledger: detect an allegiance/role
   antonym (`allied↔opposed`, `commands↔follows`) asserted near a character pair in chapter N+1
   that contradicts the pair's relationship as established in prior prose, with no bridging
   sentence. Deterministic, cheap, and it reads where the breaks are. Hard part: anchoring "the
   established prior relationship" without an LLM — may need the ledger as the *baseline* and the
   *prose* as the *contradiction surface* (ledger says `romantic_bond`; Ch5 prose puts Gunnar's
   shield in front of the enemy → contradiction).
2. **Ledger-fidelity gate as a GENERATIVE fix first (inverts measure-first, but honest).** Make
   the writer commit a relationship op whenever prose changes an allegiance, so the ledger
   actually records the flip; THEN a ledger-reversal detector has signal. This is the
   `derive_overlay`-style "give the ledger teeth" path and is a larger change.
3. **Reject ledger-vs-prose semantic judging** stays correct (that is `book_reviewer`'s job).

**Verdict.** REJECTED as specified — the detector reads `world_state.relationships` +
`character_state_deltas`, both empirically stable/empty at the flagged seams, so it cannot see
the breaks and would false-positive on the one narrated transition. The PAIN is approved; the FR
returns to Plan to redesign around the **prose layer** (Path 1) or an explicit **generative
ledger-fidelity** step (Path 2). Keep the frozen-antonym discipline and the visibility-not-gate
posture — only the **input layer** is wrong. Before re-planning, land FR-544 (overlay-trail
witness): its emitted trail will make the delta sparsity that sinks this design visible in every
run, and its fixtures become the redesign's starting evidence.

**Diary seed for graduation:** `witness_layer_mismatch` — a deterministic witness must read the
same representation the defect is authored in; reading structured state to catch a prose-only
break measures the wrong invariant (ledger self-consistency, not prose-ledger fidelity).

## Judgement — Re-plan (2026-06-20) — APPROVED with conditions (C1–C4); fold before enforce

The re-plan correctly fixes the **layer error** that sank the first cut. It now (Part 2) targets
the verified root cause — the writer never emits the `update`/`invalidate` op the ledger is
designed to receive, so allegiance is *authored in prose and never recorded* — and treats the
ledger as the system of record where allegiance belongs. That is the right diagnosis and the
right home (edge-grain, not the scalar overlay; `false_duplicate` correctly avoided). Verified
against live code: `_rel_key` is type-independent (world_state.py L105) and a type `update`
**closes the old edge** (`valid_to = current_index`) and opens a new one (L329) — the bi-temporal
machinery the witness needs already exists and is honest. Approved to proceed, subject to four
conditions that must be folded into the ACs before enforce.

**C1 — Right-size the priority and stop over-claiming coverage.** The evidence table justifies
this FR with "7 of 8" breaks on the identity/allegiance rail, but the re-plan's own honest
Scope carve removes most of them: Ylva (role) and Reinmar (role) are character-grain authority
resets with *no pairwise edge to diff*, and Gunnar-vs-Bärenschädel is *collective* (no named
participant). After the carve, the ledger path addresses the **pairwise** slice only — on the
cited books that is roughly the Hilde/Gunnar bond, ~1 of the 7. The FR is currently justified by
evidence it does not address. **Fix:** demote Priority from HIGH to MEDIUM, and add one sentence
to the Summary/Value stating explicitly that this FR covers *pairwise named-edge* allegiance and
that role/collective resets (the majority of the cited breaks) remain a separate, named follow-up.
Do not let the headline number imply this mechanism catches it.

**C2 — Read the bi-temporal stamps, not adjacent snapshots.** "Diff the committed edge's
type/status across adjacent chapters by `_rel_key`" is underspecified and fragile: per `_rel_key`
there can be **multiple** edges (a closed one with `valid_to` set *plus* the current one), so
"the edge" is ambiguous, and it needs N snapshots. The ledger already gives a cleaner, localizing
signal: a recorded transition stamps `valid_from == ordinal` on the new edge and `valid_to ==
ordinal` on the closed one, and the **final chapter's committed ledger carries the entire history**
(closed edges are never dropped unless ungrounded — verified L310, parse_world_state). **Fix:**
the witness reads `valid_from`/`valid_to` stamps from a single (final) committed ledger; a
transition = a pair with a closed edge at ordinal K and a new current edge at ordinal K. This
localizes each transition to a chapter, removes the multi-edge ambiguity, and drops the
adjacent-snapshot walk. Update the docstring and the diff-AC accordingly.

**C3 — Keep Part 2's acceptance deterministic; do not gate on regeneration.** The Part 1
baseline AC (frozen `story.json` → fixed `transition_count`) is deterministic — good. But the
prose "re-running 10031-BC should raise `transition_count` toward the prose's actual flips" is
**LLM-dependent and must never appear as a gate**. **Fix:** Part 2's only acceptance is the
*prompt-content* assertion (a test asserting `chapter_close.yaml` instructs an op for stance
changes — cooling, side switch — with the grounding gate unchanged). State plainly that writer
*compliance* is a hope, not a guarantee; the witness is the ongoing fidelity gauge, not a pass/fail
on a regenerated book. Remove any wording that reads like a stochastic acceptance gate.

**C4 — Name the witness's true limit.** Part 1 counts *grounded op-emission*, not *break
correctness*: it cannot tell a correct recorded transition from a hallucinated-but-grounded one,
and it has **no per-seam break localization** for the unrecorded flips that are the whole problem
(by the FR's own evidence it will read ~1 on a 7-break book). That is acceptable *as a regression
gauge for Part 2*, but the FR must say so — the witness complements the LLM reviewer, it does not
replace its localization. **Fix:** add one line to the Value/limitations making this explicit so
the sparse number is never misread as an all-clear (`plausible_wrong_answer` guard).

**What is explicitly NOT required:** the prose-grain detector (Path 1 of the prior judgement) is
*not* in scope here — the re-plan chose Path 2 (generative ledger-fidelity), which is a legitimate
and arguably more durable choice (it documents allegiance in the ledger rather than re-deriving it
from prose every run). Carry the frozen-antonym discipline and visibility-not-gate posture as
specified. Sequence unchanged: **land FR-544 first** (its overlay-trail makes the delta sparsity
this design depends on visible per-run), then enforce this with C1–C4 folded in.

**Verdict.** APPROVED with conditions. The mechanism now reads and writes the layer the defect
lives in, and the root cause (missing writes) is correctly targeted. Fold C1–C4 into Status,
Priority, Summary, and the Acceptance Criteria, then proceed RED-first.

## Implementation (2026-06-20) — Enforced

- **RED** `4c561f77` (`SKIP=pytest`): `examples/dungeon_master/tests/test_allegiance_ledger.py` —
  grounded reversal counted, ungrounded reversal flagged, static-ledger → 0, empty doc additive,
  non-roster pair ignored, no mutation, additive witness block, and the C3 prompt-content assertion.
- **GREEN** (this commit): new leaf `examples/dungeon_master/api/allegiance_ledger.py` with
  `allegiance_transitions(doc)` — reads the final committed `world_state.relationships`, groups by
  the type-independent `_rel_key`, detects a closed edge (`valid_to == K`) reconciled into a new
  edge (`valid_from == K`) crossing a frozen opposed stance-pole pair; `transition_count` = grounded
  reversals, `ungrounded_count` = citation-less ones; roster lens; pure. Wired into `write_witness`.
  **Part 2:** `chapter_close.yaml` now requires an `update`/`invalidate` op for stance changes (side
  switch, cooling), not only bare type turns. Imports `world_state` only (leaf); <160 lines.
- **C1** Priority demoted HIGH→MEDIUM; coverage-honesty paragraph added (pairwise slice ~1/7).
  **C2** witness reads `valid_from`/`valid_to` stamps from the final ledger, not adjacent snapshots.
  **C3** Part 2 acceptance is the deterministic prompt-content test only — no regeneration gate.
  **C4** limitation documented in the module docstring (grounded op-emission, not break correctness;
  low count ≠ all-clear).
- **Deviation (measured, material):** the baseline AC assumed `transition_count == 1` on 10031-BC
  (Hilde/Gunnar enmity→romantic_bond). Re-measuring the **final** Ch8 ledger under C2 found 3 edges,
  all `valid_to=None`, **no closed edge** — so the real reading is **0**: the writer recorded *zero*
  bi-temporal transitions despite 7 prose flips. The "1" was an artifact of the rejected adjacent-
  snapshot method. Baseline AC + fixture corrected to assert 0 (the total fidelity gap). `outputs/`
  is gitignored, so the baseline is pinned via a committed synthetic fixture mirroring that shape.
- 379 DM tests pass. Changelog: `changelog/unreleased/fr545-allegiance-ledger-witness.md`. Diary:
  `docs/diary/diary-2026-06-20-the-ledger-that-recorded-nothing.md`.
