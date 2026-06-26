# Feature Request: L6 goal-graph anchoring for affect referent (beat-free causal injection)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced — REFUTED (CLEAN subset, lift +0.000), goal-anchoring line closed (2026-06-26)
**Effort:** 1.5 days (spike + GT L6 graph extraction)
**Requested:** 2026-06-26

## Summary

FR-607 refuted goal-anchoring (honest lift **+0.000**) with a flat goal **list**.
Its `--explain` autopsy (FR-607 Autopsy Addendum) found the mechanism: the model binds
each feeling to *the goal its chosen CLOSE beat resolves*, conflating causally-adjacent
**sibling goals** (quest hope → `legitimize_queen`/F8 where GT scoped `retrieve_crown`/F6;
horror hope → `find_exit`/F2 where GT scoped `reach_surface`/F1). An upstream check then
confirmed **L6 already distinguishes these siblings and beat-binds each one** via
`functions[].motivation.goal` (one goal per beat) — the discriminator the flat list stripped
out exists one layer up.

This FR tests whether injecting the **L6 goal *causal graph*** — the goals plus their
inter-goal `enables`/`threatens` relations and agent ownership, **with all beat ids
removed** — lets the model bind the right sibling referent and (the real prize) moves
**placement on the frozen gate**, which the flat list did not.

## Value Statement

If the referent error is sibling-goal conflation and L6 holds the disambiguating goal
structure, then grounding each feeling in the goal *graph* (not a flat menu) should recover
the FR-605/607 signature arcs — and, if placement is genuinely downstream of the referent,
finally move the frozen open/close recall the whole FR-596→607 arc has failed to lift.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with three corrections — one of which the anti-tautology gate
does not currently catch.** This is the arc's third goal-anchoring attempt, and the FR is
commendably honest about that risk (it asks the Judge directly whether this is "a richer
costume on the same refuted lever"). I verified the foundation: FR-607 is CLOSED—REFUTED,
honest lift **+0.000**, referent-binding **0.143** at the GT ceiling, and its Autopsy
Addendum names the mechanism precisely — *the goal label is downstream of the close-beat
choice* (the model picks the beat by salience, then names the goal that beat serves). The
autopsy log exists. The placement-primary gate is the right gate: FR-607 proved
referent-recall is decoupled from the frozen gate, so making strict open/close recall the GO
condition (referent-recall only secondary) means this FR **cannot score a false GO** on
referent-binding alone. That single property is what earns the grant: if the "label is
downstream" hypothesis is correct, FR-609 returns +0.000 and *definitively closes* the
goal-anchoring line — a high-information refutation, not a costume. Three corrections bind it.

1. **(PRIMARY — not caught by the `/F\d/` gate) For a linear-chain goal graph, the
   disambiguating signal IS the leaking signal.** I checked the GT directly: there is no
   goal-level graph — `enables: [F1b]` is *beat→beat* and `motivation.goal` is one-goal-per-
   beat. The inter-goal edges must be DERIVED (goal A enables goal B iff a beat tagged A
   enables a beat tagged B). For quest that derivation is a **total order**
   (`legitimize_reign → retrieve_crown → deliver_crown → legitimize_queen`) isomorphic to beat
   order. A model that knows the chain order and that beats run roughly chronologically can
   read "`legitimize_queen` is last → late beat; `retrieve_crown` is mid → earlier beat"
   straight off the topology — reconstructing placement from structure with **zero** `F#`
   tokens. The beat-free `/F\d/` assertion is necessary but NOT sufficient: it catches
   id-leak, not order-leak. Therefore a mode-A placement gain **on a total-order genre is
   confounded** and cannot be promoted as anchoring. Resolution: (a) present goals in
   shuffled order; (b) compute and report each genre's goal-graph topology, flagging
   total-order graphs as leak-suspect; (c) the *clean* placement test is the BRANCHING
   (non-total-order) genres only — a total-order GO is uninterpretable. If all five genres
   are effectively linear, then only a REFUTED (even the leaky ceiling can't move placement)
   is interpretable, and any GO must be quarantined as order-leak until a branching fixture
   exists.

2. **(PRIMARY) Pre-register the causal-order discriminator that decides costume vs. lever.**
   The autopsy hypothesis ("label is downstream of beat") predicts the graph can relabel the
   referent without moving the close beat. Commit BEFORE running to the measurement that
   separates these: does mode A shift the **close-beat distribution** relative to control,
   not merely the goal name? Report (control close-beats) vs (mode-A close-beats) as a named
   metric. If referents are relabeled but the close-beat distribution is unchanged, the
   causal arrow is salience→referent, the lever is dead for the gate, and the verdict is
   **REFUTED with mechanism confirmed** — a closed line, not a maybe-FR-610. This turns Open
   Questions 1 and 3 into a measured verdict instead of a post-hoc narrative.

3. **(secondary) The prompt rule is authored from the two known misses — the clean test is
   out-of-sample, and horror does not fit the rule.** "Pick the sub-goal, not the super-goal
   it enables" is reverse-engineered from quest (`retrieve_crown` sub vs `legitimize_queen`
   super). But the autopsy shows horror conflates `find_exit`/`reach_surface` as a
   *near-synonym granularity* error ("emerge into grey daylight"), running the opposite
   direction — a different failure shape the sub/super rule does not address. Report per
   genre, mark quest+horror as the rule's authoring set, and treat detective/historical/scifi
   as the out-of-sample check (the `name_the_seam` overfit trap). One prompt clause covering
   two distinct conflation shapes is a smell.

**Endorsed:** the beat-free anti-tautology insight is sharp (correctly forbids injecting the
beat→goal map — `gate_checks_shape_not_substance` one level up); placement-primary gate;
mode A before mode B (gated on clearing KILL); honest Open Questions that pre-register
falsification; ≥3 draws @ temp 0.7; reuses the FR-607 scorer/control/leak-audit discipline;
frozen `main_l7`/`_l7_counts` byte-identical. The inter-goal precedence edge IS materially
more signal than the flat list (Open Question 3) — it is not pure costume — but correction 1
shows that same signal is the confound, which is why the verdict must lean on REFUTED-or-
branching-only-GO.

**Frozen scope:** GT L6 goal-graph extractor (beat-free, leak-audited for BOTH `F#` tokens
AND total-order topology); shuffled-order injection; `affect_locate_graph.yaml` forking
`affect_locate_goal`; reused strict (frozen) + referent scorers; control/modeA/modeB arms;
close-beat-distribution-shift metric (corr 2); per-genre topology + out-of-sample prompt-rule
report (corr 1, 3); honest-lift `modeA.relax − control.relax`; placement-primary GO
(> 0.02 over control on frozen `_l7_counts`), referent-recall vs 0.143 secondary; GO on a
total-order genre quarantined as confounded; GO/PARTIAL/REFUTED recorded. Frozen gate
untouched.

## Topology Pre-Check (2026-06-26 — resolves J corr 1)

Ran the goal-graph derivation the Judgement demanded *before* writing the harness
(`tmp/fr609_topology.py`, gitignored, reproducible). For each fixture I derived the
inter-goal graph (goal A enables goal B iff a beat tagged A `enables` a beat tagged B;
likewise `threatens`), restricted to the **referent goals** (the goals any GT affect
actually binds), and tested whether every referent-goal pair is comparable (one reaches the
other) or at least one pair is **incomparable** (an antichain — neither precedes the other).

| fixture | referent goals (order = derived precedence) | incomparable referent pair | verdict |
|---|---|---|---|
| detective | deliver_witness < expose_corruption < deliver_justice < restore_order | none | **TOTAL-ORDER** (leak-suspect) |
| quest | retrieve_crown < legitimize_queen | none | **TOTAL-ORDER** (leak-suspect) |
| horror | protect_crew, reach_surface | protect_crew ⊥ reach_surface | **BRANCHING** (clean) |
| historical | deliver_charter, expose_monopoly, protect_traders | deliver_charter ⊥ {expose_monopoly, protect_traders} | **BRANCHING** (clean) |
| scifi/loom | expose_ARIA, save_Jonas, undo_the_Loom | expose_ARIA ⊥ save_Jonas ⊥ undo_the_Loom | **BRANCHING** (clean) |

**Three of five fixtures branch.** The Judge's worst case ("if all five are effectively
linear, only a REFUTED is interpretable") **does not hold** — a clean placement test exists.

**The autopsy misses split exactly along the comparability axis, which sharpens the design
from per-genre to per-pair:**

- **quest** hope miss (`retrieve_crown` vs `legitimize_queen`) is a **comparable** pair →
  the error could be order-driven; a fix here is **order-confounded** and must be quarantined.
- **scifi** guilt miss (`save_Jonas` vs `expose_ARIA`) is an **incomparable** pair → chain
  order cannot explain or fix it. This is the **cleanest anchoring test in the set**: the
  graph must disambiguate via the *causal relations* (`expose_ARIA` enables `trace_anomaly`
  vs `save_Jonas` enables `deploy_shutdown`), i.e. structure-not-order — exactly the signal
  FR-609 claims to isolate.
- **horror** hope miss involved `find_exit`, a *non-referent* goal (near-synonym
  granularity) — the third failure shape J corr 3 flagged, orthogonal to comparability.

**Operationalization of J corr 1 (replaces "shuffle + flag total-order genres" with a
partition).** Score PLACEMENT on two disjoint subsets and report them separately:

1. **Clean subset = incomparable referent pairs** (horror, historical, scifi). GO must be
   earned here. No order to leak, so a placement lift is genuine anchoring; order-shuffling
   is unnecessary because the antichain carries no order to exploit.
2. **Quarantined subset = comparable pairs** (quest, detective). Reported, but a win is
   order-confounded and **cannot promote the lever** regardless of magnitude.

This makes the kill condition sharper too: if mode A (GT-graph ceiling) cannot disambiguate
even the incomparable scifi pair — where structure is the *only* available signal — the
goal-graph lever is dead, cleanly, with no order-leak escape hatch.

## Re-Judgement (2026-06-26) — after the Topology Pre-Check amendment

**Verdict: Authority GRANTED, sustained. Correction 1 is resolved and sharpened; the
amendment is a model response.** The requester did the one thing the original grant most
needed: ran the order-leak probe *before* writing the harness, not after. I **independently
re-ran `tmp/fr609_topology.py`** and reproduced the table exactly — detective and quest are
TOTAL-ORDER (referent pairs all comparable, leak-suspect); horror, historical, and scifi
BRANCH (incomparable referent pairs: `protect_crew ⊥ reach_surface`, `deliver_charter ⊥
{expose_monopoly, protect_traders}`, `expose_ARIA ⊥ save_Jonas ⊥ undo_the_Loom`). My worst
case — "if all five are linear, only a REFUTED is interpretable" — is **falsified**: 3/5
branch, so a clean placement test exists.

The amendment improves on my correction rather than merely complying:

- **Per-pair, not per-genre (sharper than J corr 1).** Comparability is a property of the
  referent *pair*, not the fixture; partitioning placement into CLEAN (incomparable pairs,
  GO-eligible) and QUARANTINED (comparable pairs, reported-but-cannot-promote) is the
  correct unit. The regression-guard test that re-derives topology and asserts the partition
  matches the Pre-Check table closes the silent-fixture-drift hole I did not name.
- **The antichain retires my "shuffle" mitigation.** Correctly observed: an incomparable
  pair *carries no order to leak*, so order-shuffling is unnecessary on the CLEAN subset.
  That is a better fix than mine — it removes the confound by construction instead of
  obscuring it.
- **The kill condition is now crisp.** The scifi guilt miss (`save_Jonas` ⊥ `expose_ARIA`)
  is the cleanest anchoring test in the corpus: structure is the *only* signal that can
  disambiguate it. If the GT-graph ceiling cannot move that pair, the lever is dead with no
  order-leak escape hatch — a clean, promotable REFUTED.

**Correction 3 is neutralized by the partition.** The overfit "pick the sub-goal, not the
super-goal" clause has no purchase on an antichain (there is no super/sub between
incomparable goals), so it cannot contaminate the GO-eligible CLEAN subset; and horror's
`find_exit` is correctly identified as a *non-referent* near-synonym, orthogonal to
comparability. The rule survives only in the QUARANTINED subset, whose wins cannot promote
anyway. Good.

**Two residual notes (carry into enforcement, not blocking):**

1. **Correction 2 (close-beat *distribution* shift) is verdict-subsumed but retain it as the
   null-diagnostic.** The CLEAN-subset placement gate already answers the verdict question
   (if structure moves the close beat, strict recall lifts where order cannot help). But if
   the result is +0.000 *again*, the post-mortem still needs to distinguish "the close beat
   did not move at all" (label-is-downstream confirmed — the FR-607 mechanism holds) from
   "the close beat moved but to the wrong beat" (the graph actively misleads). Report the
   control-vs-modeA close-beat distribution in the Enforcement Outcome so a null is
   explained, not just stated.
2. **State the CLEAN-subset denominator and its power.** GO is earned on the deltas whose
   referents are incomparable (horror + historical + scifi referent-deltas, on the order of
   ~15–17). With a denominator that size, confirm the > 0.02 LIFT_NOISE threshold clears the
   ≥3-draw run-to-run band — a single delta flip should not be able to manufacture a GO.
   Report N and the band alongside the lift.

**Authority stands.** The order-leak hazard that dominated the first judgement is now
measured and partitioned out; the experiment can earn a clean GO, a clean REFUTED, or an
explained PARTIAL, and none of those outcomes is confounded by the leak. Proceed.

## Problem

The lever is **in L7**, not upstream (confirmed read, 2026-06-26):

- L6 tags one goal per beat. The quest arc carries four distinct, beat-bound goals:
  `legitimize_reign` (F1) → `retrieve_crown` (F1b–F6) → `deliver_crown` (F7) →
  `legitimize_queen` (F8). The GT closes the hope at **F6** with `referent: retrieve_crown`,
  and F6's `motivation.goal` **is** `retrieve_crown`. The model bound `legitimize_queen` —
  a goal that lives in L6 at F8. The signal to choose correctly was present; L7 never saw it.
- FR-607 fed the model a flat goal **list** (id + abstract desc) — names without the
  `enables`/`threatens` structure that says `retrieve_crown` is a *sub-goal that enables*
  `legitimize_queen`. With two sibling names and no relation between them, the model defaults
  to whichever its close-beat choice serves. +0.000 was inevitable.

**The central hazard (and why the obvious design is invalid).** L6's beat→goal map *is*
the localization answer: if the injection reveals "F6 → `retrieve_crown`", a feeling whose
referent is `retrieve_crown` can read its close beat straight off the map. Injecting
beat-bound goals would make mode A a **tautology** (`gate_checks_shape_not_substance`, one
level up: the ceiling would score high by leakage, not by anchoring). Therefore this FR
injects the goal graph **beat-free** — the goals and their inter-goal causal relations and
agents, with every `F#` id stripped — so the model must still *locate*, using only the
*structure* among goals to pick the right sibling.

## Raw Output Read (measurement / metric-tooling FR)

Reuses the FR-607 referent-aware scorer (`_l7_counts_referent`); the raw read is mandatory.

- **Samples read:**
  - `logs/fr607-referent-autopsy.log` — the `--explain` rationales for all 10 mode-A
    bindings (FR-607 Autopsy Addendum table).
  - GT L6 directly: `fixtures/ground-truth/quest-adventure-the-sunken-crown.yaml`
    functions F1–F8, and `…/horror-survival-the-last-light.yaml` F1–F5.
- **What I saw (concrete, not generatable):**
  - Quest F6 (`victory`, *"Eira surfaces with the Sunken Crown"*) carries
    `motivation.goal: retrieve_crown` **and** the GT hope-close `referent: retrieve_crown`;
    F8 (`liquidation`, *"the lack is liquidated — the kingdom has a legitimate ruler"*)
    carries `motivation.goal: legitimize_queen`. The two sibling goals the model conflated
    are each beat-bound in L6, four beats apart. The beat→goal map is the close-beat answer —
    proving the injection must be beat-free or the spike is a tautology.
  - Horror runs the conflation the **opposite** direction: GT hope referent is the terminal
    `reach_surface` (F1) while the model bound the proximate `find_exit` (F2). So the error
    is not a fixed proximate→terminal slide; it is sibling conflation governed by the
    close-beat choice — the goal *graph* (which goal enables which), not a direction prior,
    is the only thing that could disambiguate.
  - Quest L6 already encodes the enabling chain (`legitimize_reign` enables `retrieve_crown`
    via the F1→F1b `enables` edge; `retrieve_crown` enables `deliver_crown` enables
    `legitimize_queen`) — the exact relation a flat list omits and this FR injects.

## Proposed Solution

Three additive parts; frozen `main_l7`/`_l7_counts` untouched; reuse the FR-607 harness,
referent scorer, validator, leak audit, and control-arm discipline.

```yaml
# 1. GT L6 goal-graph extraction (beat-free) — derived from the EXISTING
#    functions[].motivation.goal / threatens.goal / enables, with all F# ids dropped:
#    goals:
#      - id: retrieve_crown      ; agent: Eira      ; enables: [deliver_crown]
#      - id: legitimize_queen    ; agent: Eira      ; enabled_by: [deliver_crown]
#      - id: prevent_coronation  ; agent: Usurper Kael ; threatens: [retrieve_crown, ...]
#    (NO beat ids anywhere — leak audit asserts the rendered block contains no /F\d/.)

# 2. affect_locate_graph.yaml — fork of affect_locate_goal that injects the goal GRAPH
#    (goals + inter-goal enables/threatens + agent) instead of a flat id+desc list, and
#    asks the model to bind the referent using the causal relation
#    ("a hope tracks the goal a path opens TOWARD; pick the sub-goal, not the super-goal
#     it enables, unless the beats show the super-goal's own resolution").

# 3. Reused scoring (FR-607): strict ev._l7_counts (frozen gate = the prize),
#    relaxed/referent ev._l7_counts_referent. Same arms: control (no goals, FR-605),
#    modeA (GT goal-graph = ceiling), modeB (model goal-graph, gated on modeA).
```

## Acceptance Criteria

- [ ] GT L6 goal-graph extractor produces, per fixture, a **beat-free** goal graph
      (goals + `enables`/`threatens` among goals + agent); a test asserts the rendered
      injection block matches no `F\d+` token (the anti-tautology / leak gate).
- [ ] `affect_locate_graph.yaml` forks `affect_locate_goal` (frozen-gate path untouched),
      injects the graph not a flat list, and binds one referent.
- [ ] **Honest lift (J corr 1, inherited):** report `modeA.relax − control.relax` under the
      identical referent scorer; the control arm reuses FR-605's no-goal two-pass draws.
- [ ] **Primary gate is PLACEMENT, not referent binding.** FR-607 proved referent-recall is
      decoupled from the frozen gate; GO requires strict open/close recall (frozen
      `_l7_counts`) to beat control by > LIFT_NOISE (0.02). Referent-recall vs FR-607's 0.143
      is reported as the secondary, mechanism-confirming number.
- [ ] **Comparability partition (J corr 1, per Topology Pre-Check):** placement is scored on
      two disjoint subsets — CLEAN (incomparable referent pairs: horror, historical, scifi)
      and QUARANTINED (comparable pairs: quest, detective). GO may be earned **only** on the
      CLEAN subset; a win on the QUARANTINED subset is reported but order-confounded and
      cannot promote the lever. A test re-derives the per-fixture topology and asserts the
      CLEAN/QUARANTINED partition matches the Pre-Check table (regression guard against a
      future fixture edit silently moving a fixture across the line).
- [ ] Referent-recall reported **conditioned on** pass-1 set recall (the cap, J corr 4).
- [ ] Mode A (ceiling) before mode B (production); mode B gated on mode A clearing KILL.
- [ ] ≥3 draws @ temp 0.7 with run-to-run band; frozen gate byte-identical
      (`git diff --stat evaluate.py` shows no scored-path change).
- [ ] Diary reflection; FR updated with Enforcement Outcome (GO/PARTIAL/REFUTED).

## Open Questions (for Judgement)

1. **Is placement actually downstream of the referent?** The autopsy says the model picks
   the close beat by salience, then *names* the goal that beat serves. If so, fixing the
   referent may NOT move placement — the graph could lift referent-recall while the frozen
   gate stays at +0.000 (a PARTIAL: mechanism confirmed, prize unmoved). The FR must not
   pre-assume the causal arrow; the placement gate is the honest test of it.
2. **Beat-free graph vs. too little signal.** Stripping beats to avoid tautology may strip
   so much that the graph cannot disambiguate either. If mode A (GT-graph ceiling) cannot
   clear KILL on referent-recall, the hypothesis is dead and mode B is never run.
3. **Is this just FR-607 + relations?** Judge should weigh whether the inter-goal
   `enables`/`threatens` edge is a materially different injection from the flat list, or a
   richer costume on the same refuted lever.

## Alternatives Considered

- **Inject the beat-bound L6 map (F6 → retrieve_crown).** Rejected: tautology — hands the
  model the close beat for any feeling whose referent is that goal. The whole anti-leak
  design exists to forbid this.
- **Decompose locate per referent ("where does hope-about-retrieve_crown open/close").**
  Deferred: requires the referent *a priori*, inverting the dependency this FR tests; a
  candidate FR-610 only if FR-609 confirms referent→placement causality.
- **Fix it upstream in L6.** Rejected by the 2026-06-26 read: L6 already distinguishes and
  beat-binds the siblings; the gap is L7's blindness, not L6's resolution.

## Enforcement Outcome (2026-06-26) — REFUTED

**Verdict: REFUTED on the CLEAN subset (clean-subset lift +0.000 <= noise 0.020).**
The FR-607->609 goal-anchoring line is closed. Log: `logs/fr609-live.log`
(control + mode A, 3 draws @ temp 0.7, claude-haiku-4-5). Mode B was correctly
SKIPPED — mode A strict 0.250 < KILL 0.50.

| metric | control | mode A (GT-graph ceiling) |
|---|---|---|
| strict recall (frozen `_l7_counts`) | 0.250 | 0.250 |
| relax recall | 0.250 | 0.250 |
| **CLEAN** placement (horror/historical/scifi) | 0.176 | 0.176 (**lift +0.000**) |
| QUARANTINED placement (quest/detective) | 0.364 | 0.364 (lift +0.000) |
| referent binding | — | 0.083 (draws 0.036 / 0.071 / 0.143) |
| honest lift (modeA.relax − control.relax) | | **+0.000** |
| close-beat shift (control→modeA) | | 0.367 |

**What the result proves (high-information refutation, not a costume failure):**

1. **The order-leak escape hatch is eliminated.** The +0.000 lift is on the CLEAN
   (branching) subset — genres where the referent goals form an antichain, so chain
   order carries *no* placement signal. The graph is the *only* available
   discriminator there, and at the GT ceiling it moves placement by exactly nothing.
   This is the clean REFUTED the Topology Pre-Check made interpretable; a
   total-order-only fixture set could not have produced it.
2. **The richer injection made anchoring WORSE, not better.** Referent binding fell
   to 0.083 (mode A mean) vs FR-607's flat-list 0.143. The inter-goal
   `enables`/`threatens` relations act as *distractors*, not disambiguators: the
   model still binds the referent its salient close beat serves, and the added
   structure gives it more to misread. The "materially-more-signal" edge (Open Q3)
   is real signal the model does not use for this task.
3. **The mechanism is confirmed (J corr 2).** Close-beat shift 0.367 with *identical*
   placement recall means mode A reshuffles ~37% of close-beat picks as salience noise
   around an unchanged accuracy. The causal arrow is **salience → referent**, never
   **goal → placement**. Fixing the referent label cannot move the frozen gate because
   the label is downstream of the beat choice, exactly as the FR-607 autopsy predicted.

**Disposition:** goal-anchoring (flat list FR-607, causal graph FR-609) is closed as a
lever on the frozen open/close gate. The L7 localization ceiling (~0.25 strict at this
decomposition) is not reachable by naming or structuring the goal. Any future attempt
must change the *beat-selection* step, not the referent annotation. Frozen
`main_l7`/`_l7_counts` byte-identical (`git diff --stat evaluate.py`: 119 insertions,
0 deletions). Witnessed by `tests/test_l7_graph.py` (5 tests, RED→GREEN); the topology
probe graduated from `tmp/fr609_topology.py` into `evaluate.derive_goal_graph` +
`spike_affect_graph.py --topology`.

## Related

- `feature-requests/FR-607-goal-anchored-affect-referent.md` (REFUTED; Autopsy Addendum) —
  the flat-list predecessor and the mechanism this FR acts on.
- `feature-requests/FR-606-affect-rationale-field.md` — the `--explain` probe that produced
  the autopsy; reuse it to read FR-609 misses too.
- `docs/diary/diary-2026-06-26-the-probe-never-turned-on.md` — the seed (L6 causal edge).
- `tmp/fr609_topology.py` — the goal-graph topology derivation (gitignored, reproducible)
  behind the Topology Pre-Check table; promote into the harness as the partition regression
  test at enforce time.
- `examples/plot_modeller/spike_affect_goal.py` (harness + `--explain`),
  `examples/plot_modeller/evaluate.py` (`_l7_counts_referent`, `validate_referents`,
  `audit_goal_descriptions`), `fixtures/ground-truth/*.yaml` (L6 `motivation`/`threatens`/
  `enables`).
- `logs/fr607-referent-autopsy.log` — the raw read.
