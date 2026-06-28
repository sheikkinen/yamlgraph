# Feature Request: FR-599 L7 Affect Recall — Miss Decomposition Probe (investigation)

**Priority:** HIGH
**Type:** Investigation (Bug) — read-only diagnostic; no production behavior change
**Status:** Enforced — probe built + fixture-pinned; verdict **MULTI-CAUSE** ((e) UNLICENSED and (a) ABSENT tied at 39%); successor FRs named (2026-06-26)
**Effort:** ~0.5 day (one throwaway probe script + one corpus run; no graph, no evaluator change)
**Requested:** 2026-06-26
**REQ:** REQ-YG-020 (reuse — no new CAP)
**Predecessor:** FR-598 (kill the novel — Enforced, hypothesis REFUTED: the terse classifier
*regressed* the gate, `detection` 0.52 → 0.24, `affect_recall` 0.15 → 0.06)
**Gate (frozen, untouched):** FR-578 `affect_recall ≥ 0.50` (`main_l7` in `evaluate.py`)
**Reserved escalation this FR routes:** FR-578 model scale **vs** six-kind taxonomy revision
**vs** evaluator beat-matching tolerance / GT granularity **vs** GT re-annotation /
cross-beat context (the UNLICENSED case — the input itself does not license the affect)

## Summary

FR-598 spent the one permitted format iteration and refuted the prose-is-the-cause
hypothesis, leaving the reserved escalation pointing at *three* different levers (model
scale, taxonomy, evaluator/GT granularity) with no evidence for which one is correct.
Before spending compute on a bigger model or scope on a taxonomy rewrite, this FR builds
a **read-only miss-decomposition probe**: for every ground-truth affect delta the frozen
gate scores as a miss, classify *why* it missed into five mutually exclusive buckets
(UNLICENSED checked first — the input does not license the affect at all). The dominant
bucket names the lever. This is the `investigation_before_fix` cure — build the harness
that proves the causal split first; the fix FR that follows is mechanical.

## Value Statement

The L7 team stops guessing which reserved lever to pull: instead of a hunch-driven
haiku→sonnet corpus run, the probe shows whether the recall floor is a *model* ceiling
(model can't see the affect), an *evaluator artifact* (right affect, off-by-one beat id),
or a *taxonomy* ceiling (right beat, wrong kind) — each implying a different, and very
differently priced, next FR.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED.** This is the right move at the right moment: the
`investigation_before_fix` cure applied to a refuted hypothesis that left three
differently-priced levers unseparated. Building the harness that proves the causal
split before spending model compute or taxonomy scope is exactly the FR-371→372
discipline. Claims verified: FR-598 is **Enforced — REFUTED** with the cited numbers
(`affect_recall` 0.15→0.06 WORSE, `detection` 0.52→0.24 COLLAPSED — "the format
change lost the arcs the prose used to catch"); `_affect_matches`, `_match_count`,
`_l7_counts`, `_load_gt_affects` all exist; the diary `the-novel-was-also-the-net`
exists. This is also the **first FR to use the new `## Raw Output Read` template
section**, and it used it as intended — concrete surprises a generated dump could not
produce (Marren's `loss` on F2-not-F1, The Swarm's surviving `betrayal → Jonas`,
horror's near-total absence of `close` ops). The enforcement loop closed.

**Corrections required before enforce (do not widen scope):**

1. **The exact-beat-id miss definition lives in `_l7_counts`, NOT `_affect_matches`
   (PRIMARY — accuracy).** I read the code: `_affect_matches` is beat-id-*agnostic*
   (op/kind/char/toward only). The gate enforces exact beat id structurally in
   `_l7_counts`, which keys predictions by `bid` and compares each GT beat only
   against `pred_by_id.get(bid, [])`. So importing `_affect_matches`/`_load_gt_affects`
   alone does **not** reproduce the gate's miss set — the probe must replicate (or
   import) `_l7_counts`'s beat-keyed grouping to define "miss" identically, then relax
   the beat key to ±N only for the BEAT-OFF lens. Add a **tie-out assertion**: the
   probe's reconstructed exact-beat hit count must equal `main_l7`'s reported
   `recall_hits` on the same input, before any bucket is trusted. That makes "miss
   identically to the gate" verifiable, not asserted, and ties the conservation check
   to the *actual* gate.

2. **Report buckets as a function of the neighbor window (±1 / ±2 / ±3), not a single
   ±2 (PRIMARY).** The ABSENT↔BEAT-OFF boundary routes between the **most expensive**
   lever (model scale) and the **cheapest** (evaluator tolerance), and that boundary
   is entirely determined by the window. A ±2 cut that finds "BEAT-OFF dominates" may
   only be measuring a generous window. Show the sensitivity: if BEAT-OFF dominates
   even at ±1 the evaluator-tolerance lever is robust; if only at ±2 the verdict must
   say so and rank the lever weaker.

3. **Split every bucket by `op` (open vs close) (PRIMARY).** The FR's own raw read
   found the classifier under-emits `close` ops. A missing `close` falls into ABSENT
   — which routes to *model scale* — but the real cause is the format: FR-598 deleted
   the "every arc must close" mandate, and "the novel was also the net" — removing it
   lost real closures with the invented ones. So an ABSENT bucket dominated by `close`
   misses points back at arc-handling/format, **not** at a model ceiling, and a bigger
   model on the same close-suppressing classifier would repeat it. Without the op-split
   the probe routes the close-suppression confound to the most expensive wrong lever.
   Report ABSENT-open vs ABSENT-close explicitly.

4. **Make `kind`-match REQUIRED for BEAT-OFF (b), not parenthetical (secondary).** A
   same-`op`+`char` neighbor with a *different* `kind` is not "the same affect one
   beat away" — counting it inflates the cheap evaluator lever. Require kind-match on
   the neighbor; demote a kind-mismatched neighbor to ABSENT (the exact affect is
   present nowhere nearby).

**Minor:** define ABSENT as the explicit residual (anything not b/c/d) so the
conservation check is structural, not coincidental; and carry the window-sensitivity
+ op-split into the **named successor** so it inherits disambiguated evidence, not a
bare bucket label. REQ-YG-020 reuse, frozen `main_l7` untouched, successor-named-not-
written — all correct, endorse.

**Frozen scope:** the read-only `probe_l7_misses.py` consuming the FR-598 classifier
output + GT, replicating `_l7_counts` to tie out to the gate, emitting the
four-bucket decomposition **× window (±1/±2/±3) × op (open/close)** with the
conservation check and ≥3 dumped+read miss records, ending in one named dominant
lever (or "multi-cause → split successors"). No evaluator change, no model run, no
taxonomy edit, no gate-tolerance change — those are the successor's, decided on this
probe's evidence.

**Requester amendment (2026-06-26, post-judgement — add bucket (e) UNLICENSED).** Reading
the actual GT beats (not just the model output) exposed a fifth, prior failure mode the
four buckets cannot see: the GT anchor beat's *own gloss* sometimes does not license the
affect at all. Detective Marren's GT `open loss` is anchored to **F1** — whose subject is
*Hagen* and whose text never names Marren ("Hagen's hired men abduct Witness Pell … burn
the building"); the licensing text ("Marren … **discovers** the witness is gone … the case
**collapses**") sits on **F2**, where GT places no affect. And Marren's GT
`hidden_blessing` (F7→F8) is licensed by *no* beat: F7 is a clean "the court acknowledges
Marren's evidence," with no setback-that-proves-a-gift anywhere in the gloss. So a
per-beat model grounded in the beat's own words (exactly what FR-598 mandates) **cannot**
recover these by construction. Add **(e) UNLICENSED**, evaluated *first*, decided by an
explicit LLM-or-human licensing pass over (GT delta, anchor gloss), with a
`neighbor_licensed` sub-flag separating *causal→experiential displacement* (signal on a
nearby beat — GT anchors the cause, the model reads the manifestation) from *true
under-determination* (signal nowhere). Its lever is GT re-annotation or a cross-beat
context window — distinct from model scale, taxonomy, and gate tolerance. This widens the
frozen scope by one bucket and one licensing pass; all four corrections above still bind.

## Re-Judgement (2026-06-26) — after the UNLICENSED amendment

**Verdict: Authority GRANTED, with two binding corrections governing the new licensing
pass.** The original judgement stands; the amendment improves the probe and is endorsed.

**Concession first.** My original grant read the code and the FR-598 numbers but did not
read the GT beats. The requester did, and found a real fifth failure mode the four-bucket
scheme is structurally blind to. I verified it against the fixture: GT `open Marren loss`
is anchored to **F1**, whose subject is *Hagen* and whose gloss ("Hagen's hired men abduct
Witness Pell … burn the building") never names Marren; the licensing manifestation
("Marren … discovers the witness is gone … the case collapses") sits on **F2**, where GT
places no affect. And `open Marren hidden_blessing` rides **F7**, a clean positive
("the court acknowledges Marren's evidence") with no setback-that-proves-a-gift anywhere
in the gloss. Both are underivable from the anchor beat's own words — exactly the
grounding FR-598 mandates. This is the `read_raw_output_first` discipline applied one
layer deeper than I applied it: to the GROUND TRUTH, not the model output. Bucket (e) is
a **correctness fix, not scope creep** — without it, every UNLICENSED miss is mis-routed
to ABSENT → *model scale*, the single most expensive lever, and a bigger model reading F1
would correctly still not emit Marren-loss. The `neighbor_licensed` sub-flag is the
load-bearing distinction: F1-loss is `neighbor_licensed=True` (cause on F1, manifestation
on F2 → cross-beat-context lever); F7-hidden_blessing is `neighbor_licensed=False` (signal
nowhere → GT re-annotation lever). The two route to *different* successors, so the flag
must be explicit per (e) record.

**Corrections 1–4 from the original judgement all still bind.** The amendment adds two:

5. **Pin the licensing pass to the hand-found cases as fixtures (PRIMARY).** The LLM-or-
   human licensing pass is the *only* un-validator-covered component now entering a
   previously deterministic, tie-out-checked probe — it is the new flood surface. Do not
   trust it blind. The two cases the requester already adjudicated by hand become
   known-answer fixtures the pass MUST reproduce or the probe fails: F1 `loss` →
   UNLICENSED, `neighbor_licensed=True`; F7 `hidden_blessing` → UNLICENSED,
   `neighbor_licensed=False`. This is the FR-594 "witness against a known-positive"
   pattern: a judge you cannot calibrate against a known answer is not evidence.

6. **(e) is the motivated-reasoning bucket — gate it conservatively and spot-check every
   member (PRIMARY).** Of the five buckets, (e) is the convenient exit: ABSENT →
   "buy a bigger model" costs compute; UNLICENSED → "the GT is wrong" costs nothing and
   exonerates both model and taxonomy. A licensing pass even slightly biased toward
   "underivable" will preferentially drain misses into (e) and manufacture a false
   "it's a data problem" verdict that ends the escalation prematurely. So (e) must be the
   most conservatively gated of the five — default to NOT-unlicensed unless the affect is
   *clearly* underivable from anchor + neighbors — and because it should be small (the
   Marren story yields ~2), a human reads **every** (e) classification, not a sample.
   The Red Hat challenge the FR must answer in its output: the licensing LLM is doing a
   per-beat affect judgement, the same task class the L7 classifier fails at 0.09 — it is
   admissible only because it is *recognition with the GT answer given* (not generation),
   it is fixture-pinned (correction 5), and every positive is human-read.

**Interaction with correction 1 (tie-out).** Unchanged and still required: the tie-out is
on the HIT side (`probe hits == main_l7 recall_hits`). The MISS side now partitions into
five buckets with (e) skimmed FIRST; the conservation check becomes
`hits + (a)+(b)+(c)+(d)+(e) == GT total`. (e)-first ordering is correct: if the GT does
not license the affect, no bucket below it is meaningful.

**Frozen scope (restated):** the read-only `probe_l7_misses.py` consuming the FR-598
classifier output + GT, replicating `_l7_counts` to tie out hits to the gate, skimming
**(e) UNLICENSED first** (fixture-pinned, conservative, every member human-read, with
`neighbor_licensed` set per record), then emitting the four-bucket decomposition
**× window (±1/±2/±3) × op (open/close)** over the residual, with the five-bucket
conservation check and ≥3 dumped+read miss records, ending in one named dominant lever
(or "multi-cause → split successors"). No evaluator change, no model run for scoring, no
taxonomy edit, no gate-tolerance change. The only new judgement surface is the licensing
pass, and corrections 5–6 fence it.

## Problem

The FR-598 enforce read of the raw classifier output surfaced a concrete clue the
aggregate hid: detective protagonist **Marren's `loss` lands on F2 in BOTH the prose and
the classifier, but GT says F1** — an off-by-one beat-id miss. The frozen gate's
`detection` axis requires *exact* beat-id equality (`_affect_matches` / `_match_count` in
`evaluate.py`), so a correctly-read affect placed one beat away scores as a total miss.
We do not know how much of the 0.06–0.15 recall floor is this kind of artifact versus a
genuine model failure versus a kind-discrimination ceiling. Three candidate root causes,
zero measurement separating them.

Worse, a *fourth* cause hides beneath all three: some GT deltas are not licensed by their
anchor beat at all. GT anchors affect to the **causal** beat (F1: Hagen abducts the
witness → `Marren loss`) while the text that *shows* the feeling sits on the
**experiential** beat (F2: "Marren discovers … the case collapses"), and some kinds
(`hidden_blessing` at F7) are licensed by no gloss at all. A per-beat model grounded in
the beat's words — FR-598's own rule — cannot reach these, so charging them to "model
failure" would scale a bigger model against an impossible target. The probe must separate
this UNLICENSED case (bucket (e), evaluated first) from genuine model misses.

## Raw Output Read (measurement / metric-tooling FRs only)

`read_raw_output_first` — this probe is metric tooling, so the FR-598 raw reads that
motivate it are cited here (dumped to disk under
`examples/plot_modeller/results/l7/throughlines/<genre>/<agent>.yaml`,
log `logs/fr598-classifier-spike.log`):

- **Samples read:** `detective.../Marren.yaml`, `scifi.../The_Swarm.yaml`, and the four
  `horror-survival-the-last-light/*.yaml` files.
- **What I saw (one concrete surprise per sample):**
  - `Marren.yaml` emits only `F2 open loss` and `F6 close retaliation` — GT has 8 deltas
    for Marren; the `loss` is on **F2 where GT says F1** (off-by-one, not absent).
  - `The_Swarm.yaml` (a rat hive-mind, not a person) still got authored a `betrayal →
    Jonas` plus a `loss` open/close pair — invention survived the format change, but at
    far lower volume (3 ops vs the prose novel's ~6).
  - `horror/*.yaml`: every agent emitted exactly 1–2 ops, all `open`, almost no `close`
    — the classifier under-emits closes specifically, which a recall gate punishes.
- **GT beats read directly** (`fixtures/ground-truth/detective-thriller-the-vanished-witness.yaml`,
  printed with each beat's `eff_affect`):
  - GT `open Marren loss` is anchored to **F1** whose subject is **Hagen** and whose
    gloss never names Marren — the affect is **unlicensed at its own anchor**, while the
    licensing text sits one beat later on F2 (causal→experiential displacement).
  - GT `open Marren hidden_blessing` at **F7** ("the court acknowledges Marren's
    evidence") has **no setback-that-proves-a-gift** anywhere in the gloss — the *kind*
    is licensed by no beat, only by genre/arc inference. Truly under-determined.

These are reads a generated dump could not produce; they are why the probe targets
beat-alignment and op-balance, not just kind.

## Proposed Solution

A throwaway, **read-only** probe `examples/plot_modeller/probe_l7_misses.py` that reuses
the FR-598 classifier pipeline output (`results/l7/<genre>.yaml`) and the GT affects, and
for every GT delta the frozen gate counts as a miss, assigns exactly one bucket:

| bucket | test (each MISS, checked in order e→a→b→c→d) | implied reserved lever |
|--------|-------------------------------------|------------------------|
| **(e) UNLICENSED** *(first)* | the GT anchor beat's own gloss does not license this affect/kind to a careful reader (LLM-or-human judged). Sub-flag `neighbor_licensed`: signal on a beat within ±N (causal→experiential displacement) vs nowhere (true under-determination) | **GT re-annotation / cross-beat context** — the input cannot yield it per-beat; not model scale, not taxonomy |
| **(a) ABSENT** | licensed at anchor, but no predicted delta with this `op`+`char` on the GT beat or any kind-matched neighbor within ±N | model scale (FR-578) — model truly misses a licensed affect |
| **(b) BEAT-OFF** | a predicted delta with same `op`+`char`+`kind` on a neighbor within ±N, not the exact GT beat | evaluator beat-matching tolerance / GT granularity |
| **(c) KIND-WRONG** | predicted `op`+`char` on the EXACT GT beat, but `kind` differs | six-kind taxonomy revision |
| **(d) TOWARD-WRONG** | predicted `op`+`char`+`kind` on the exact GT beat (relational kind), but `toward` differs | prompt/taxonomy relational-direction gap |

Rules:

- **Mutually exclusive, checked in order (e)→(a)→(b)→(c)→(d)**; UNLICENSED first so the
  input's own failure is never charged to the model. ABSENT is the explicit residual
  (anything not e/b/c/d). Conservation is checked on the HIT side per correction #1:
  `hits + (a)+(b)+(c)+(d)+(e) == GT total`, with `hits == main_l7 recall_hits`.
- **Tie-out to the actual gate (correction #1).** Replicate `_l7_counts`'s beat-keyed
  grouping to define "miss" identically; assert the reconstructed exact-beat hit count
  equals `main_l7`'s reported `recall_hits` on the same input before any bucket is
  trusted. `_affect_matches` alone is beat-id-agnostic and does not reproduce the gate.
- **Window sweep (correction #2).** Report every bucket × window ±1/±2/±3; the
  ABSENT↔BEAT-OFF boundary (and UNLICENSED's `neighbor_licensed` sub-flag) is
  window-determined, and it routes between the most and least expensive levers.
- **Op-split (correction #3).** Split every bucket by `op` (open/close). An ABSENT
  bucket dominated by `close` points at FR-598's deleted arc-closure mandate
  ("the novel was also the net"), **not** a model ceiling — report ABSENT-open vs
  ABSENT-close explicitly.
- **Kind-match required for BEAT-OFF (correction #4).** A same-`op`+`char` neighbor with
  a different `kind` is not the same affect one beat away; demote it to ABSENT.
- **Licensing pass — fixture-pinned (correction #5).** UNLICENSED is decided by an
  explicit LLM-or-human judgment over (GT delta, anchor gloss + ±N neighbors), not the
  agent's say-so. It is the *only* new judgement surface entering an otherwise
  deterministic, tie-out-checked probe — the new flood surface — so it is pinned to the
  two hand-adjudicated cases as known-answer fixtures it MUST reproduce or the probe
  fails: Marren **F1 `loss` → UNLICENSED `neighbor_licensed=True`**; Marren
  **F7 `hidden_blessing` → UNLICENSED `neighbor_licensed=False`**. A judge uncalibrated
  against a known answer is not evidence (FR-594 witness-against-known-positive).
- **(e) is the motivated-reasoning bucket — gate it conservatively, read every member
  (correction #6).** (e) is the convenient exit: ABSENT costs compute, UNLICENSED costs
  nothing and exonerates both model and taxonomy, so a pass even slightly biased toward
  "underivable" manufactures a false "it's a data problem" verdict that ends the
  escalation early. Default to **NOT-unlicensed** unless the affect is *clearly*
  underivable from anchor + neighbors; because (e) is small (~2 for the Marren story) a
  human reads **every** (e) classification, not a sample. The pass is admissible only
  because it is *recognition with the GT answer given* (not generation — unlike the L7
  classifier it does not have to produce the affect, only judge whether the named one is
  derivable), it is fixture-pinned, and every positive is human-read; per-delta verdicts
  are dumped to disk for that audit.
- **Frozen evaluator untouched.** The ±N neighborhood and the licensing pass are
  *diagnostic lenses*; they add no tolerance to the gate itself.
- **Forced raw read:** before printing the aggregate, the probe dumps ≥3 miss records
  (GT delta + anchor gloss + nearest predicted delta + licensing verdict) to
  `results/l7/miss-samples.txt` and the verdict line asserts they exist to be read.
- **Verdict:** name the dominant bucket and the single implied lever; if no bucket holds
  > 50% the conclusion is "multi-cause — split the successor FRs," not a coin-flip.

## Acceptance Criteria

- [x] `probe_l7_misses.py` emits the **5**-bucket decomposition (counts + % of misses),
      pooled, **× window (±1/±2/±3) × op (open/close)**, with the conservation check
      (`hits + buckets == GT total`, asserted per window) and the `_l7_counts` tie-out
      assertion (reconstructed exact-beat hits == gate `recall_hits`, asserted per genre).
- [x] Bucket **(e) UNLICENSED** is decided by an explicit LLM licensing pass over
      (GT delta, anchor gloss + ±2 neighbors), with the `neighbor_licensed` sub-flag,
      and the per-delta verdicts dumped to disk; Marren's F1 `loss` (neighbor-licensed)
      and F7 `hidden_blessing` (under-determined) both land in (e).
- [x] **Licensing pass is fixture-pinned (correction #5):** it reproduces the
      hand-adjudicated known answers — F1 `loss` → UNLICENSED `neighbor_licensed=True`,
      F7 `hidden_blessing` → UNLICENSED `neighbor_licensed=False`, **plus the close-op
      fixture F5 `close loss` → LICENSED** (added when reading every (e) exposed an
      open-biased judge) — or the probe FAILS (it did, twice, until calibrated).
- [x] **(e) is conservatively gated (correction #6):** default LICENSED unless clearly
      underivable, and **every** (e) member (12, not a sample) is human-read, with
      verdicts dumped to `results/l7/unlicensed-members.txt`. This read is what caught
      the close-op miscalibration and flipped the verdict from single-cause to multi-cause.
- [x] ≥3 miss records dumped to disk and read before the aggregate is trusted
      (`read_raw_output_first`); the Marren `F1`/`F2` displacement appears in the set.
- [x] The probe prints the dominant bucket and the named reserved lever (or "multi-cause"
      if none > 50% — which fired), carrying the window-sensitivity and op-split.
- [x] Frozen FR-578 `main_l7` evaluator is **not** modified (verified by diff — untouched).
- [x] No new CAP; REQ-YG-020 reused. (Probe is a throwaway harness, no unit tests added.)
- [x] Changelog fragment (`changelog/unreleased/`, `req: REQ-YG-020`) + diary reflection.
- [x] Successor FRs named (not written) below, so this FR closes as a *decision*.

## Enforcement Outcome (2026-06-26)

**Verdict: MULTI-CAUSE.** The 0.06 `affect_recall` floor is not one defect. Pooled over
five genres (33 GT deltas, 2 gate hits, 31 misses), at window ±2:

| bucket | misses | % | open/close | named lever |
|--------|-------:|--:|-----------|-------------|
| (e) UNLICENSED | 12 | 39% | 9 / 3 | GT re-annotation / cross-beat context |
| (a) ABSENT | 12 | 39% | 6 / 6 | model scale (FR-578) |
| (c) KIND-WRONG | 5 | 16% | 1 / 4 | six-kind taxonomy (close-op kind confusion) |
| (b) BEAT-OFF | 2 | 6% | 2 / 0 | evaluator beat tolerance / GT granularity |
| (d) TOWARD-WRONG | 0 | 0% | — | (none) |

Conservation holds at every window (`2 + 31 == 33`); the per-genre `_l7_counts` tie-out
passed (reconstructed hits == gate `recall_hits`). No single lever clears 50%, so pulling
one — the naive gate reading would scale the model (a) — would leave ~61% of the floor
untouched.

**The calibration is the headline.** The first run's licensing pass was open-biased
("does the text *show* the feeling?"), which mis-judged every `close` op and reported
(e) at **55% — DOMINANT**, a single-cause "the GT is wrong" verdict. Reading **every** (e)
member (correction #6) — not a sample — surfaced the bug: a `close` is licensed by the
feeling's *resolution* (a recovery/triumph), not its presence. Adding a `close`-op fixture
(F5 `close loss` → LICENSED) and an op-branched prompt moved 5 misses out of (e), tying it
with (a) and flipping the verdict to MULTI-CAUSE. The two open-op fixtures alone had
certified the uncalibrated judge; only the mandated full read caught it. Correction #6 was
load-bearing, not ceremonial.

**Op-split routing (correction #3):** (a) ABSENT is op-balanced (6/6), so the FR-598
arc-closure deletion is *not* the dominant ABSENT cause — re-adding the mandate would not
clear the floor (consistent with the FR-598 refutation). (c) KIND-WRONG is close-heavy
(4/1): the model *places* a close op+char on the right beat but mis-kinds it — a taxonomy/
discrimination gap, not silence.

**Window sensitivity (correction #2):** (e) and (c) are window-independent (anchor-exact).
(a) ABSENT 12→12→9 and (b) BEAT-OFF 2→2→5 as the window widens ±1→±3 — ~3 "model-scale"
misses are recoverable by evaluator tolerance at ±3, so (a)'s true size depends on the
gate's beat strictness.

**Successor FRs named (not written):**
- **FR-600 — GT affect re-annotation (experiential anchoring).** Move each GT delta from
  its *causal* beat to the *experiential* beat that licenses it (F1→F2 displacement), and
  drop or down-weight the truly under-determined kinds (F7 `hidden_blessing`). Largest,
  cheapest lever; a data fix, no model spend. Evidence: (e) = 39%, open-heavy (9/3),
  `neighbor_licensed` split in `unlicensed-members.txt`.
- **FR-601 — L7 close-op kind discrimination.** Address the close-heavy (c) KIND-WRONG
  (4/1): the model closes on the right beat with the wrong kind. Taxonomy clarification or
  a close-specific classifier hint, *not* model scale. Evidence: (c) = 16%, close 4 / open 1.
- **FR-602 — gate beat-tolerance experiment (gated, conditional).** Only if FR-600 leaves
  residual (a)/(b): measure `affect_recall` at a ±1 beat tolerance against the
  re-annotated GT, since (b) grows 2→5 at ±3. Touches the frozen gate, so it is a
  separately-judged *fix*, never bundled here.

Model scale (FR-578) is **deferred**: (a) is only 39% and partly dissolves into (b) at
wider windows, so it is the most expensive lever against the smallest clearly-model share.
Measure-first held — the probe stopped a premature sonnet corpus run.

## Alternatives Considered

- **Skip straight to FR-578 model scale (haiku→sonnet corpus run).** Refuted by cost
  asymmetry: if the dominant bucket is BEAT-OFF, a bigger model writes the same
  off-by-one and the spend is wasted. Measure first, then scale only if bucket (a) wins.
- **Loosen the gate's beat matching to ±1 directly.** Premature — that is a *fix*, and
  changing the frozen FR-578 gate without first proving BEAT-OFF dominates would be the
  `downstream_fix` trap (editing the ruler to flatter the model). The probe proves the
  cause; a separate, judged FR may then change the gate or the GT.
- **Treat the UNLICENSED misses as model failures (the pre-amendment framing).** Refuted
  by the GT read: F1 `loss` (anchor names only Hagen) and F7 `hidden_blessing` (no
  setback-gift in any gloss) cannot be recovered by a beat-grounded model no matter the
  scale — scoring them as model misses would route the most expensive lever at an
  impossible target. They need GT re-annotation or a context window, which only bucket
  (e) surfaces.
- **Re-read every throughline by hand.** Does not scale to 24 agents × 5 genres and
  produces no conservation-checked tally; the probe mechanizes the read the way the
  diary seed (`forced-observation gate`) intends.

## Related

- Predecessor: [`FR-598-l7-affect-throughline-kill-the-novel.md`](FR-598-l7-affect-throughline-kill-the-novel.md)
  (Enforcement Outcome — the refutation + the Marren off-by-one read)
- Evidence: [`FR-598-evidence/langsmith-trace-throughline-vs-encode.md`](FR-598-evidence/langsmith-trace-throughline-vs-encode.md)
- `examples/plot_modeller/evaluate.py` (`_affect_matches`, `_match_count`, `_load_gt_affects`,
  `main_l7` — imported read-only, never modified)
- `examples/plot_modeller/spike_affect.py` (FR-598 classifier whose output the probe consumes)
- Diary: [`docs/diary/diary-2026-06-26-the-novel-was-also-the-net.md`](../docs/diary/diary-2026-06-26-the-novel-was-also-the-net.md)
  (the flood-vs-silence bracket that motivates bucket (a) vs (b))
- Scripture cures: `read_raw_output_first`, `investigation_before_fix`, `downstream_fix` (trap)
