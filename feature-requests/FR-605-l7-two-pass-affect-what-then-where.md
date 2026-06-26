# Feature Request: L7 two-pass affect detection (what-then-where)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** CLOSED — REFUTED (2026-06-26)
**Effort:** 1 day (spike)
**Requested:** 2026-06-26

## Summary

Split the L7 protagonist affect classifier into two passes: **pass 1 names the
unordered SET of emotions the protagonist carries** across the arc; **pass 2
locates each named emotion's open beat and close beat** as two distinct beats.
The single-pass classifier collapses an emotion's endpoints onto the single most
salient beat; decomposing "what" from "where" attacks that collapse directly, and
makes pass 1 the natural gate that keeps zero-support emotions (retaliation,
hidden_blessing) from ever emitting — the support-gating FR-604 left as a
candidate, achieved by construction instead of a threshold.

This supersedes the earlier "support-gated six-kind sweep" FR-605 candidate. The
localization autopsy (below) showed the binding constraint is beat-placement, not
which kinds run, so the re-scope follows the evidence.

## Value Statement

The L7 gate (protagonist affect recall) is the last KILL stage in the plot-modeller
evaluation; raising it from 0.214 toward the 0.50 REVISE line is the one lever left
after character, budget, precision, per-kind decomposition, and model-scale were
each eliminated by measurement.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with four corrections.** This is the best-targeted FR of the
arc: every cheaper lever has been spent and *measured* away, and the re-scope from the
original support-gated sweep to two-pass follows the evidence rather than a hunch. I
verified the full evidence base against the artifacts — FR-604 CLOSED (arm A KEPT precision
0.375, arm B REFUTED 0.243 < 0.375 with recall +0.107, `multi-recovered []` every draw,
retaliation 0/18 + hidden_blessing 0/27 = 100% of the precision violation); the Sonnet log
(recall 2/28 = 0.07 < haiku 0.214, detection 0.29 — a bigger model localized *worse*,
correctly read as falsifying scale, not the log's stale "scale justified" line). And I
**independently reconstructed the localization autopsy** from the draw1 dumps: 26
supported-kind GT, 9 hits, 17 misses, **wrong_beat 12 (71%)**, dropped 2, off_by_one 2,
op_flipped 1 — exact. Only 2/17 are near-misses, so the tolerance window is correctly
rejected and the failure is genuine mis-placement. The design is well-aimed and pass 1
subsumes support-gating *by construction* (a kind it never names cannot flood) — the
elegant fix to arm B's refutation cause. Four corrections bind the grant.

1. **The "two DISTINCT beats, obligatory pair" obligation over-corrects collapse into forced
   invention — soften it (PRIMARY).** The verified failure is *collapse* (endpoints fused
   onto the salient beat). But mandating an obligatory distinct open+close pair (a) cannot
   represent the GT's own same-beat cases — scifi `F9` places `open hope` AND `close hope`
   on one beat (the flare-then-die moment), which the obligation would make unscoreable;
   and (b) forces a close beat for emotions the text opens but never resolves, reviving the
   FR-598 invention engine one level up — a fabricated-but-plausible close is a *dishonest
   hit* the precision guard may not catch (it only lands as a precision loss if the invented
   beat is wrong; a plausible wrong-place close inflates recall). Pass 2 must **locate open
   and close independently** — each may be a distinct beat, the same beat, or absent —
   grounded in the text, with the anti-collapse pressure phrased as "consider the endpoints
   separately; do not default both to the most dramatic beat," NOT as "they must differ."

2. **Measure pass-1 SET recall separately so a miss is attributable to set vs placement
   (PRIMARY).** Two-pass makes pass-2 localization conditional on pass-1 naming the kind:
   a kind pass 1 omits is unrecoverable downstream. Report pass-1 protagonist set recall
   (did it name every GT kind?) as its own number, so a disappointing final recall is
   diagnosable as a set-detection miss vs a localization miss — the same arm-A/arm-B
   attribution discipline this arc has already paid to learn. Without it, a REFUTE can't be
   routed to the right pass.

3. **Confirm the pass-2 arc skeleton is derived from gloss structure, not the affect GT
   (secondary).** The setup/turn/resolution anchor is a legitimate structural cue only if
   computed from beat position/sequence (which the model already sees); if any of it is
   GT-derived it leaks the answer. State the derivation explicitly in the spike.

4. **Persist the localization autopsy as a committed artifact (secondary).** It is the
   central justification, and I had to reconstruct it from the gitignored draw1 dumps to
   verify it. Commit it like `fixtures/affect-licensing/l7-absent-decomposition.md` (the
   FR-603 precedent) so the 71% premise is durable, not ephemeral.

**Endorsed:** targets the one verified failure mode (wrong_beat 71%, independently
reproduced), pass-1 set-gate fixes arm B's zero-support flood by construction (not a
threshold), scale falsified on the Sonnet probe, tolerance window correctly rejected
(2/17 near), frozen `main_l7` byte-identical, production prompt forked-not-deleted, ≥3-draw
temp-0.7 noise-floor discipline, precision benchmarked against arm A's 0.375 (not the 0.12
merged artifact) and recall against 0.214.

**Frozen scope:** the two-pass spike (`affect_set` + `affect_locate`) replacing the L7
spike emit only, reporting pass-1 set recall, pass-2 localization, and final corpus recall
+ per-kind precision over ≥3 draws; open/close located independently (same/distinct/absent
permitted, text-grounded); at least one previously-collapsed arc (quest hope F6, horror
loss F1/F6) recovered as a named hit; a committed autopsy artifact; GO/REVISE/REFUTED with
the revert rule (recall up but precision below arm A 0.375 = REFUTED). Frozen gate
untouched.

## Enforcement Outcome (2026-06-26)

**Verdict: REFUTED.** Two-pass beat recall but missed the precision floor, and the
two specifically-named collapse arcs did not recover. Stable across 3 draws @ temp 0.7
(`logs/fr605-twopass-3draws.log`):

| metric | arm A (baseline) | two-pass (mean of 3) | result |
|---|---|---|---|
| corpus recall | 0.214 (6/28) | **0.250 (7/28)** | +0.036 |
| corpus precision | **0.375 (6/16)** | 0.368 (7/19) | **VIOLATED** (-0.007) |
| pass-1 SET recall | n/a | 0.500 (9/18) | new upper bound |

- **The localization hypothesis was directionally CONFIRMED but insufficient.** The
  aggregate collapse share dropped from **71% to 39% of misses** (wrong_beat 22/57),
  exactly as the autopsy predicted — splitting "what" from "where" does relieve endpoint
  fusion in aggregate. But it bought only +0.036 recall and sat the precision **0.007
  below arm A's floor**, so by the frozen revert rule (recall up, precision below arm A
  0.375) this is REFUTED. The single-pass char-pinned arm A remains the kept production
  classifier.
- **The two named hard arcs did NOT recover (AC-3 specific clause unmet).** quest hope
  still emitted `open F4 / close F8` (GT close is F6 — pinned to the crown beats again);
  horror loss still emitted `open F4 / close null` (GT F1 open / F6 close — collapsed onto
  the dramatic beat and dropped the close). The arcs the autopsy singled out as the
  collapse signature were unmoved; the aggregate improvement came from easier arcs (hope
  precision 0.62, 15/24).
- **The bottleneck relocated upstream to pass-1 SET recall (correction-2 payoff).** Pass 1
  named only **half** the GT protagonist kinds (0.500). That is a hard ceiling: pass-2
  localization can only lose from there, so even perfect placement caps final recall at
  ~0.50 of GT. The disappointing final recall is therefore **attributable to set-detection,
  not (only) placement** — exactly the routing the separate-set-recall correction was added
  to enable. The next lever, if any, is pass-1 recall, not pass-2 placement.
- **Invention largely suppressed by the set gate, not eliminated.** retaliation emitted
  nothing (0 preds — pass 1 correctly withheld it), vindicating support-gating-by-
  construction over arm B's 0/18 flood. hidden_blessing still over-emitted (2/draw, 0/6
  correct) — pass 1 named it (it has 1 GT instance) but pass 2 mis-placed it.
- **Frozen gate byte-identical** (`git diff --stat` on `evaluate.py` +
  `affect_throughline.yaml` empty); production prompt forked, not replaced.

The arc's conclusion: every lever — character, budget, precision, per-kind decomposition,
model-scale, and now what-then-where localization — has been spent and *measured*. L7
recall's binding constraint is now pass-1 set detection (0.50), and the gate stays at arm
A's 0.214. No production change ships from this spike.

### Prose-grounded post-mortem: the misses are referent mismatch, not drift

Reading the two named hard arcs against their actual beat prose (not just beat ids) changed
the diagnosis. The model does not place a correctly-identified emotion on a *random* beat;
it attaches the right **kind** to a different but **textually-valid event** than the
annotator chose.

- **Quest hope, model `F4/F8` vs GT `F4/F6`.** Open agrees (F4, the breathing reed). The
  close splits on *which hope*: GT closes at F6 (*"Eira surfaces with the Sunken Crown"* —
  the quest object obtained); the model closes at F8 (*"places the Crown on Queen Livia's
  head ... the lack is liquidated"* — the kingdom saved, the beat GT labels `close guilt`).
  The model closed the **narrative's terminal** hope, GT the **protagonist's proximate**
  hope. Both grounded.
- **Horror loss, model `F4/null` vs GT `F1/F6`.** The model and GT disagree about *what the
  loss is*. GT loss = entrapment: opens F1 (*"a collapse seals the main shaft ... trapped"*),
  closes F6 (*"feels moving air — a ventilation shaft"*, the way out found). Model loss =
  bereavement: opens F4 (*"the Watcher takes him ... Fen is gone"*), never closes (`null` —
  an honest read; a death does not resolve). The model located *its* loss perfectly; it is a
  **different loss object**. (F4 is where GT places `open guilt` — same beat, the model read
  its affect as loss, not guilt.)

**Consequence for the design.** The `wrong_beat` bucket (39% of misses) masks a **referent
mismatch**: kind correct, the *event the emotion is about* differs, and both anchors are
text-valid. Two-pass cannot fix this, because pass 2 faithfully locates whatever pass 1
names — and pass 1 names `loss`/`hope` **without a referent**. The missing signal is *which*
loss, not *where* it sits. The real next lever is therefore **referent-anchoring** (pass 1
or the GT must name the object/event each emotion attaches to, and scoring must accept any
text-valid anchor), not better beat-placement prompting. This is why aggregate collapse
improved (71%->39%) while the signature arcs stayed "wrong" — those arcs are not mislocated,
they are differently-referred.

## Problem

L7 `affect_recall` sits at **0.214 (6/28), KILL** and every prior lever has been
spent:

- **Precision** was a merged-roster scoring artifact; char-pinning fixed it
  (0.12 -> 0.375, FR-604 arm A, kept).
- **Budget** is not binding; removing the one-op-per-beat cap recovered zero
  multi-delta beats (FR-604, `multi-recovered []` every draw).
- **Per-kind decomposition** with equal detectors was REFUTED: it lifted recall
  +0.107 but precision fell to 0.243 because the two zero-support kinds invented
  (retaliation 0/18, hidden_blessing 0/27) (FR-604 arm B).
- **Model scale** does not help (see Raw Output Read: Sonnet did *worse* than haiku).

What remains is a single, measured failure mode: **right emotion, wrong beat.**
The model knows the protagonist feels loss/hope/guilt but places the open/close on
the wrong beat — usually collapsing both endpoints onto the most salient beat.

## Raw Output Read (measurement / metric-tooling FRs only)

Two probes were run before authoring; both read the raw artifacts, not just scores.

- **Samples read:**
  - Per-kind dumps `examples/plot_modeller/results/l7_perkind/throughlines/draw1/<genre>/<kind>.yaml`
    (loss/hope/guilt/betrayal across 5 genres), classified vs ground truth.
  - Sonnet single-pass throughlines + `logs/fr604-sonnet-ceiling.log`.

- **Localization autopsy (draw1, protagonist, kinds loss/hope/guilt/betrayal):**
  26 GT deltas, 9 hits, 17 misses, bucketed by *how* each miss failed:

  | bucket | count | share of misses |
  |---|---|---|
  | wrong_beat (right kind, far beat) | 12 | 71% |
  | dropped (kind never emitted) | 2 | 12% |
  | off_by_one (adjacent beat) | 2 | 12% |
  | op_flipped (right beat, wrong open/close) | 1 | 6% |

- **What I saw (concrete, not generatable):**
  - quest `F6 close hope`: the model emitted `F4 open` + `F8 close` — it pinned
    hope's endpoints to the two crown beats and never placed the close at F6 where
    Eira actually relinquishes the crown. The arc was *shifted onto the climax*.
  - horror: two distinct loss deltas (`F1 open`, `F6 close`) were **fused into a
    single `F4 open`** — a story-spanning arc compressed to one dramatic beat.
  - Sonnet, same prompt: emitted 30 predictions, only **2 correct** (recall 0.071
    vs haiku 0.214); even kind-blind beat-placement was only 0.29 (8/28). A larger
    model did not localize better — it localized worse. This is a framing problem,
    not a capability ceiling.

  Only 2/17 misses were near-misses, so a tolerance window is worthless; the
  failure is genuine mis-placement, which is what the two-pass split targets.

## Proposed Solution

Two LLM passes per protagonist, replacing the single `affect_throughline` emit for
the L7 spike (production prompt forked, not deleted, per FR-604 precedent).

```yaml
# Pass 1 - the SET (what). Cheap, invention-guarded.
# prompt: affect_set
# in:  protagonist, glosses (plain-text beats)
# out: { kinds: [loss, hope, guilt] }   # unordered, only kinds with textual support
#      Default is the EMPTY set. No kind without grounding in the beats.

# Pass 2 - the ENDPOINTS (where), one emotion at a time.
# prompt: affect_locate
# in:  protagonist, kind (one), glosses, beat arc structure (setup/turn/resolution)
# out: { open: <beat_id|null>, close: <beat_id|null> }
#      open and close are located INDEPENDENTLY and text-grounded. Each may be a
#      distinct beat, the SAME beat, or absent (null) when the text opens an
#      emotion it never resolves (or vice versa). (J: correction 1 - the obligatory
#      distinct-pair would (a) make the GT's own same-beat cases unscoreable - scifi
#      F9 opens AND closes hope on one flare-then-die beat - and (b) force a
#      fabricated close = a dishonest recall hit, the FR-598 invention engine one
#      level up.) Anti-collapse pressure is phrased as: "consider the open and the
#      close SEPARATELY; do not default both to the most dramatic beat," NOT as
#      "they must differ."
```

- Pass 1 subsumes support-gating: a kind that pass 1 does not name never runs
  pass 2, so retaliation/hidden_blessing cannot flood (the FR-604 arm B failure).
- **Pass-1 SET recall is reported as its own number** (did pass 1 name every GT
  protagonist kind?), so a disappointing final recall is attributable to a
  set-detection miss vs a localization miss (J: correction 2 - the arm-A/arm-B
  attribution discipline; a REFUTE must route to the right pass).
- Pass 2 receives a beat arc skeleton (setup/turn/resolution) **derived purely from
  gloss beat position/sequence** - the order the model already sees - never from the
  affect GT, which would leak the answer (J: correction 3). The derivation is stated
  explicitly in the spike.
- Deterministic glue unions the located `(open, close)` beats (dropping nulls) into
  `results/l7_perkind/<genre>.yaml`-shape predictions and scores via the FROZEN
  `evaluate.py` (`_l7_counts` / `main_l7`). No gate change.
- The localization autopsy that justifies this FR is **persisted as a committed
  artifact** (not left in the gitignored draw1 dumps), per the FR-603
  `l7-absent-decomposition.md` precedent (J: correction 4).

## Acceptance Criteria

- [ ] **Beats arm A at the margin. NOT MET -> REFUTED.** Recall rose (0.250 > 0.214)
      but precision fell to 0.368, **below** arm A's 0.375 floor (stable across 3 draws).
      By the frozen revert rule, recall up + precision below arm A = REFUTED.
      Two-pass corpus `affect_recall` > arm A's
      0.214 AND corpus `affect_precision` >= arm A's 0.375, measured as the **mean
      of >= 3 spike draws** at temp 0.7 (FR-603 noise-floor discipline), reported
      with run-to-run band. A recall gain that drops precision below arm A is
      REFUTED (FR-604 precedent).
- [x] **Pass-1 SET recall reported separately (J: correction 2).** Reported 0.500
      (9/18) -> identified the new upstream ceiling. The fraction of
      GT protagonist kinds pass 1 names is logged as its own number, so a final-recall
      miss is attributable to set-detection vs localization. (This is the upper bound
      on final recall - localization can only lose from here.)
- [ ] **Collapse failure reduced (PARTIAL).** Aggregate `wrong_beat` share dropped
      71% -> 39% of misses (measurably reduced), BUT the two named hard arcs did NOT
      recover: quest hope still `F4/F8` (GT close F6), horror loss still `F4/null`
      (GT F1/F6). Aggregate drift improved; the signature collapses did not.
      The `wrong_beat` share of protagonist misses
      (71% baseline) drops measurably; at least one previously-collapsed arc
      (quest hope F6 close, horror loss F1/F6) scores as a hit, proving independent
      open/close placement worked, not just aggregate drift.
- [x] **Open/close located independently, no forced pairs (J: correction 1).** Pass 2
      may emit a distinct open+close, both on the SAME beat, or only one side (null
      the other); it is never forced to invent a close. The GT same-beat case (scifi
      F9 open+close hope) remains scoreable.
- [x] **Arc skeleton is gloss-derived, not GT-derived (J: correction 3).** The
      setup/turn/resolution anchor fed to pass 2 is computed from beat
      position/sequence only; no affect-GT field touches it. Derivation stated in
      the spike.
- [x] **No zero-support invention (mostly).** retaliation suppressed (0 preds,
      pass 1 withheld it); only 1 false name across 5 genres (historical invented
      hidden_blessing). Per-kind precision reported. retaliation and hidden_blessing emit nothing
      unless pass 1 names them from textual support; per-kind precision reported.
- [x] **Autopsy persisted as a committed artifact (J: correction 4).** The
      localization autopsy (71% wrong_beat) is written to a tracked file, not left
      in the gitignored draw1 dumps.
- [x] **Frozen gate byte-identical.** `git diff --stat` on `evaluate.py` +
      `affect_throughline.yaml` empty. `git diff --stat examples/plot_modeller/evaluate.py`
      empty; production `affect_throughline.yaml` untouched (forked, not replaced).
- [x] Two-pass spike harness + `affect_set` / `affect_locate` prompts added;
      >= 3-draw distributions logged to `logs/` and the verdict recorded in this
      FR's Enforcement Outcome.
- [x] Diary reflection added.

## Alternatives Considered

- **Tolerance window (+-1 beat).** Rejected: only 2/17 misses are adjacent
  near-misses; the gate is frozen anyway, so this is a diagnostic at best.
- **Model-scale escalation (FR-578).** Falsified by the Sonnet probe: recall
  0.071 < haiku 0.214. Bigger model does not localize better.
- **Support-gated six-kind sweep (original FR-605 candidate).** Superseded:
  fixes precision (already solved) but not the recall floor (beat-localization).
  Two-pass folds support-gating in via pass 1 for free.
- **Per-kind sweep (FR-604 arm B).** REFUTED on precision; over-emission engine.

## Related

- `feature-requests/FR-604-l7-per-kind-detection-protagonist-focus.md` (parent;
  arm A kept, arm B refuted, this FR's evidence base)
- `feature-requests/FR-603-l7-hope-emission-discrimination.md` (noise-floor
  discipline, >= 3 draws)
- `examples/plot_modeller/evaluate.py` (FROZEN gate: `_l7_counts`, `main_l7`)
- `examples/plot_modeller/spike_affect_per_kind.py` (autopsy source)
- `logs/fr604-sonnet-ceiling.log` (model-scale falsification)
- `docs/diary/diary-2026-06-26-headroom-is-not-a-lever.md` (FR-604 reflection)
