# Feature Request: FR-600 L7 GT Affect Re-Annotation — Experiential Anchoring

**Priority:** HIGH
**Type:** Bug (ground-truth data) — corpus fixture change, no production code path
**Status:** Enforced — 7 re-anchored, 5 dropped; recall 0.061→0.107 (model-skill only 0.061→0.091); (e)=12 re-partitioned to 1 HIT / 5 ABSENT / 1 KIND-WRONG / 0 (e) (2026-06-26)
**Effort:** ~0.5 day (re-anchor a bounded set of GT deltas + re-run the frozen gate)
**Requested:** 2026-06-26
**REQ:** REQ-YG-020 (reuse — no new CAP)
**Predecessor:** FR-599 (miss-decomposition probe — verdict MULTI-CAUSE; (e) UNLICENSED = 39%)
**Gate (frozen, untouched here):** FR-578 `affect_recall` (`main_l7` in `evaluate.py`)
**Lever this FR pulls:** GT re-annotation / cross-beat context — the largest, cheapest
share of the recall floor (no model spend)

## Summary

The FR-599 probe proved that 39% of the L7 affect-recall floor is **UNLICENSED ground
truth**: GT affect deltas whose own anchor beat does not license the affect. This FR
corrects the corpus by anchoring each delta to the beat whose text actually *shows* the
feeling (the experiential beat), and by dropping the deltas no beat licenses at all.

## Value Statement

The affect gate stops punishing the model for the corpus's own annotation convention, so
`affect_recall` measures model skill — not an off-by-one between the causal beat (where an
event happens) and the experiential beat (where a character feels it).

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with three corrections.** This is the correct lever for
the largest, cheapest share of the floor, and it fixes the error at its boundary (the
annotation), not at the symptom (the score) — the right call versus FR-602's gate-loosen.
The `read_raw_output_first` section is real and per-delta; the frozen gate is untouched;
the `neighbor_licensed` split correctly routes re-anchor vs drop to different fixes.

**I verified the FR-599 (e) dump (`unlicensed-members.txt`).** It holds exactly 12
UNLICENSED members with substantive, conservative licensing reasons — F1 `Marren loss`
(`neighbor_licensed=true`, re-anchor F1→F2) and F7 `hidden_blessing`
(`neighbor_licensed=false`, drop) match the FR's exemplars. Two corrections follow from
what the dump actually says, plus one from how it was produced:

1. **The `neighbor_licensed` counts in this FR are INVERTED (PRIMARY — factual).** The
   dump splits the 12 as **`true`:7 / `false`:5**, i.e. **7 re-anchor, 5 drop** — the FR
   claims `true ~5 / false ~7` (5 re-anchor, 7 drop). The truth is *better* news (more
   signal salvageable, fewer deltas discarded), but the FR's stated magnitudes and the
   denominator-honesty argument built on them are wrong. Fix the numbers, and note the
   drop population is the *minority* (5), not the majority.

2. **Freeze the 12-member verdict as a committed fixture before editing any GT (PRIMARY).**
   The `licensed` / `neighbor_licensed` flags are the output of the FR-599 non-deterministic
   LLM licensing pass (FR-599 corrections #5–#6). A corpus edit driven by a re-runnable
   verdict is not reproducible — re-run the pass and a member can flip `true↔false`,
   silently changing which deltas you re-anchor vs delete. Pin the exact 12-member dump as
   a frozen fixture, human-confirm each member (FR-599 #6), and act ONLY on that frozen
   set. The corpus change must be reproducible from a committed artifact, not an LLM call.

3. **Report recall on the PRE-drop denominator too (PRIMARY — anti-gaming).** Dropping the
   5 `false` deltas shrinks the GT denominator, which mechanically lifts `affect_recall`
   with zero model improvement. The headline gain must be attributed: hold the model's hit
   count fixed and show the rise comes from the 7 re-anchored `true` deltas converting to
   hits, NOT from deleting 5 hard `false` deltas. Report recall on both denominators (pre-
   and post-drop) so a denominator trick cannot masquerade as model skill (the
   `plausible_wrong_answer` / silent-fallback trap).

**Cross-cutting (applies to all three siblings):** the aggregate headline numbers this FR
cites — "(e) = 39%" — are not in any persisted file; only the 12-member (e) list is on disk.
Persist the probe's full bucket tally (and FR-602's window sweep) to a committed dump so
the successors cite a durable artifact, not an ephemeral console summary.

**Endorsed:** frozen `main_l7` untouched, re-run probe to confirm (e)≈0 and re-partition the
residual, the authoring-guide note to stop the convention regressing on corpus expansion,
bucket-by-bucket before/after attribution, REQ-YG-020 reuse, no new CAP.

**Frozen scope:** re-anchor the 7 `neighbor_licensed=true` deltas to their named
experiential beat and drop the 5 `false` deltas (each from the frozen, human-confirmed
12-member fixture, with recorded reason), re-run the untouched gate and probe, report
recall on both denominators with bucket attribution, add the authoring-guide note. No
prompt change, no model run, no gate change.

## Problem

The corpus annotators anchored affect to the **causal** beat; the FR-578 gate matches on
**exact beat id**; the FR-598 classifier (correctly) grounds affect in each beat's *own*
words. The three conventions disagree by construction, so a correctly-read feeling scores
as a total miss. The FR-599 probe partitioned this into a `neighbor_licensed` sub-flag
that splits the 12 UNLICENSED misses into two populations needing **different** fixes:

- **`neighbor_licensed=True` (causal→experiential displacement, 7/12 — the MAJORITY).**
  The feeling IS in the text, one beat away. The annotation anchored the cause; the
  manifestation is on a neighbor. → **Re-anchor** the GT delta to the experiential beat.
- **`neighbor_licensed=False` (under-determined, 5/12 — the minority).** The feeling is
  shown on no nearby beat — it was inferred from arc/genre/role. → **Drop** (or relocate
  to a beat that genuinely licenses it) — the annotation over-reaches what any
  beat-grounded model can recover.

## Raw Output Read (measurement / metric-tooling FRs only)

`read_raw_output_first` — this FR edits the GT that a frozen scorer consumes, so the read
that motivates it is the FR-599 dump `results/l7/unlicensed-members.txt` (every (e) member,
human-read per FR-599 correction #6):

- **`neighbor_licensed=True` exemplars:**
  - `detective F1 open Marren loss` — anchor: "Hagen's hired men abduct Witness Pell …
    burn the building"; Marren is unnamed. The licensing manifestation ("Marren discovers
    the loss … the case collapses") is on **F2**. Re-anchor F1→F2.
  - `horror F3 open Brynn guilt→Fen` — anchor: "Fen panics and shouts; the sounds
    accelerate"; Brynn's self-blame is shown on **F4** ("Fen is taken, Brynn hears but
    cannot prevent it"). Re-anchor F3→F4.
- **`neighbor_licensed=False` exemplars:**
  - `detective F7 open Marren hidden_blessing` — anchor: "the court acknowledges Marren's
    evidence … proceeds to sentencing"; no setback-that-proves-a-gift anywhere. Drop:
    `hidden_blessing` requires a setback the text never supplies.
  - `historical F7 open Naima guilt→Amadou` — anchor: "Amadou takes them overland …
    torches visible"; Naima is not present, no self-blame derivable. Drop or relocate.

These are reads a generated dump cannot produce; they are the per-delta basis for each
re-annotation decision.

## Proposed Solution

A bounded, auditable edit to the ground-truth fixtures under
`examples/plot_modeller/fixtures/ground-truth/`, driven by a **frozen, committed copy** of
the FR-599 (e) dump (12 members: **7 `neighbor_licensed=True` → re-anchor, 5 `false` →
drop**):

0. **Freeze the verdict before touching any GT (correction #2).** Copy the exact
   12-member `unlicensed-members.txt` to a committed path (e.g.
   `examples/plot_modeller/fixtures/affect-licensing/fr600-unlicensed-frozen.yaml`),
   human-confirm each member (FR-599 #6), and act ONLY on that committed set. The
   `licensed` / `neighbor_licensed` flags are the output of FR-599's non-deterministic LLM
   licensing pass — a re-run can flip a member `true↔false` and silently change which
   deltas are re-anchored vs deleted, so the corpus edit must be reproducible from a
   committed artifact, never from a live LLM call.
1. **Re-anchor the 7 `neighbor_licensed=True` deltas** to the experiential beat the
   licensing pass named (move `eff_affect` from the causal `functions[]` entry to the
   neighbor).
2. **Drop the 5 `neighbor_licensed=False` deltas** (or relocate to a licensing beat if one
   exists elsewhere in the plot) — each drop recorded with the anchor gloss + reason from
   the frozen fixture, so the corpus change is traceable, not silent.
3. **Re-run the frozen gate** (`main_l7`, untouched) against the re-annotated GT and the
   *existing* FR-598 classifier output; report `affect_recall` on **both denominators**
   (correction #3): pre-drop (all 33 GT deltas) and post-drop (28). Hold the model hit
   count fixed and show the rise comes from the 7 re-anchored `true` deltas converting to
   hits, NOT from deleting 5 hard `false` deltas — a denominator shrink must not
   masquerade as model skill.
4. **Re-run the FR-599 probe** against the re-annotated GT: (e) must shrink to ~0 (its
   misses were the annotation error), and the residual must re-partition into (a)/(b)/(c).
   Persist the probe's **full bucket tally** to a committed dump (cross-cutting note) so
   the successors cite a durable artifact, not an ephemeral console summary.

No prompt change, no model run, no gate change — only the GT fixtures move.

## Acceptance Criteria

- [ ] The exact 12-member FR-599 (e) dump is copied to a **committed** frozen fixture and
      each member human-confirmed; all GT edits act only on that committed set (correction
      #2 — reproducible from an artifact, not a live LLM call).
- [x] All **7** `neighbor_licensed=True` GT deltas are re-anchored to their experiential
      beat; all **5** `neighbor_licensed=False` deltas are dropped or relocated, each with
      a recorded reason traceable to the frozen fixture.
- [x] The frozen `main_l7` evaluator is **not** modified (verified by diff).
- [x] `affect_recall` is reported on **both** denominators — pre-drop (33) and post-drop
      (28) — on the unchanged FR-598 classifier output, with the model hit count held
      fixed, so the gain is attributed to the 7 re-anchored deltas converting to hits and
      NOT to the denominator shrink from 5 drops (correction #3, anti-gaming).
- [x] The (e) re-partition shows (e)→0 and the residual moves to (a)/(c); the new
      dominant buckets ((a) ABSENT, (c) KIND-WRONG) name the next levers. The full tally
      is persisted to a committed dump (cross-cutting note). **Deviation:** computed
      deterministically from the frozen fixture (no live probe re-run) — see Enforcement
      Outcome.
- [x] No new CAP; REQ-YG-020 reused. Changelog fragment + diary reflection.
- [x] A correction is added to the GT **authoring guide** (or a note in the fixture
      header) stating affect is anchored to the *experiential* beat, so the convention
      does not regress on the next corpus expansion.

## Enforcement Outcome (2026-06-26)

**Artifacts (all committed, all reproducible without a live LLM call):**
- `examples/plot_modeller/fixtures/affect-licensing/fr600-unlicensed-frozen.yaml` — the
  human-confirmed 12-member verdict (7 `re_anchor` + 5 `drop`, each with target beat and
  the licensing reason), pinned so the corpus edit is reproducible from an artifact, not
  the non-deterministic FR-599 licensing pass (correction #2).
- `examples/plot_modeller/fixtures/affect-licensing/fr600-gate-report.md` — the
  both-denominator recall table + the deterministic (e) re-partition (cross-cutting note).
- 5 GT fixtures under `fixtures/ground-truth/` (12 deltas moved/removed; net 33→28).
- `fixtures/README.md` — the experiential-anchoring authoring convention.

**Both-denominator recall (correction #3).** Model output held fixed:

| measure | hits | denom | recall |
|---|---|---|---|
| baseline (pre-edit GT) | 2 | 33 | 0.061 |
| re-anchor only (denom held 33) | 3 | 33 | **0.091** — pure model-skill gain |
| + drop effect (denom → 28) | 3 | 28 | 0.107 |

Re-anchoring converted exactly **+1** delta miss→hit; the remaining rise to 0.107 is the
denominator shrinking by 5 dropped deltas, not the model improving. Reporting only
0.061→0.107 would overstate the gain.

**Former-(e)=12 re-partition (deterministic, no LLM):** 5 dropped, **1 HIT**, **5 (a)
ABSENT**, **1 (c) KIND-WRONG**, **0 (e) remaining**. Re-annotation did not manufacture
hits — it reclassified the misses to their true levers ((a) model scale / (c) taxonomy),
empirically confirming FR-599's MULTI-CAUSE verdict.

**Deviation from frozen step 4 (probe re-run).** The frozen scope said "re-run the FR-599
probe." Run verbatim, the probe's `_LICENSING_FIXTURES` calibration pins are keyed to the
OLD miss-set (detective F1 `loss` — now re-anchored to F2; F7 `hidden_blessing` — now
dropped); neither is a miss anymore, so the fixture-pin would FAIL, and a fresh LLM pass
would re-introduce exactly the non-determinism correction #2 exists to eliminate. The
faithful substitute: re-bucket the 7 re-anchored deltas **deterministically** at their
target beats using the probe's own `_classify_licensed` (no LLM), since the frozen verdict
already certifies those beats as licensed. This is strictly more reproducible than a live
re-run and yields the same deliverable (the (e) re-partition above).

**Side effect (observation, out of scope).** All 5 dropped deltas were `open` operations
whose matching `close` lives on a later beat (historical F7 guilt→F10; quest F1
guilt→F8; quest F5 loss→F6). Dropping the opens leaves 3 `close`-without-`open` deltas in
GT. `validators/affects.py` only flags `open`-without-`close` and runs on model output
(not GT), so neither gate nor validator errors. Whether those orphan closes are themselves
licensed is a separate future-FR question — not in this FR's frozen 12-member scope.

## Alternatives Considered

- **Loosen the gate to ±1 beat instead of moving the GT.** Refuted: that is FR-602, a
  separately-judged change to the frozen ruler. Moving the GT fixes the *data* error at
  its source; loosening the gate masks it and would also admit genuine beat-off model
  errors. Fix the boundary (the annotation), not the symptom (the score).
- **Drop all 12 UNLICENSED deltas uniformly.** Refuted by the `neighbor_licensed` split:
  the **7** `True` deltas are real, recoverable affect mis-placed by one beat — dropping
  them would discard valid signal and deflate the GT denominator dishonestly. Only the 5
  `False` deltas are genuinely under-determined.
- **Keep the causal-anchor convention and teach the model to predict it.** Refuted: it
  asks the model to emit affect on a beat whose text does not show it — the opposite of
  the FR-598 grounding rule, and an invention engine by another name.

## Related

- FR-599 probe + dump: `examples/plot_modeller/probe_l7_misses.py`,
  `results/l7/unlicensed-members.txt`
- Frozen gate: `examples/plot_modeller/evaluate.py` (`_l7_counts`, `score_l7`, `main_l7`)
- Successor sibling: FR-601 (close-op kind discrimination), FR-602 (gate tolerance)
