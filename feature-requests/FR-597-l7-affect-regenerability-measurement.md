# Feature Request: FR-597 L7 Affect-Regenerability Measurement (the affect port of FR-594)

**Priority:** HIGH
**Type:** Feature (measurement ruler — affect port of the L5 regenerability graph)
**Status:** Judged — Authority GRANTED (2026-06-25)
**Effort:** ~1 day (mirrors FR-594; reuses its two-axis design and the `[UNDERDETERMINED]` probe convention)
**Requested:** 2026-06-25
**Predecessor:** FR-578 (L7 monolithic affect pass — affect_recall 0.09, model-invariant)
**Sibling lineage:** FR-594 / FR-595 (L5 regenerability ruler + `world_recall` demotion — the proven precedent this FR ports to affect)
**Origin:** FR-596 Gate-1 manual inspection (the "numbers lie" finding — affect_recall is the `world_recall` pathology one layer over)
**Blocks:** the protagonist-throughline encoder work (must run *after* this ruler reframes the gate) and, transitively, FR-579 (merge node)

## Summary

Port the L5 prose-regenerability ruler (FR-594) to the L7 affect layer. Build a
YAMLGraph graph that measures an L7 affect encoding by whether the **emotional
throughline is regenerable from the affect deltas alone** — emitting the same two
orthogonal axes FR-594 established: *simulability* (does the affect skeleton license
its own emotional narration, deterministically, GT-free?) and *fidelity* (does that
narration match the source synopsis's actual emotional content, via an LLM judge?).

The graph is a **diagnostic only** this cycle. `affect_recall` (the frozen FR-578
gate) stays primary; nothing is rewired to gate on the new measure. Demotion of
`affect_recall` is a *separate future FR* once this ruler has corpus history — exactly
the discipline FR-594 followed before FR-595 demoted `world_recall`.

## Value Statement

The FR-596 Gate-1 manual inspection proved `affect_recall = 0.09` is **uninterpretable
as a quality signal** — it measures token-agreement against a sparse, under-determined,
mono-perspective skeleton, not whether the emotional story was captured. This is the
identical pathology FR-594 found at L5 (`world_recall` scored agreement with a lossy
skeleton). L7 authors need a GT-free, falsifiable ruler for "did the encoding capture
the emotional arc?" *before* anyone spends model effort lifting 0.09 → 0.50 on a
number that lies. This FR builds that ruler; it does not yet swing it.

## Judgement (2026-06-25)

**Verdict: Authority GRANTED.** This is a faithful port of a *proven* ruler, and it
has pre-baked every discipline my FR-594 Judgement imposed: diagnostic-only this
cycle, witness the under-determination as a known-positive, keep the two axes
orthogonal, power-before-gate, and the Red-Hat premise check (OQ#1 — if GT scores
*low* underdetermined the thesis is refuted and `affect_recall` is **not** demoted).
Claims verified against landed state: `l5_measure.yaml` exists and its three pure
tools (`render_l5_beats`/`score_simulability`/`combine_l5_measure`) are in
`nodes/tools.py` carrying the FR-594 "DIAGNOSTIC this cycle" note, so the
node-for-node template is real, not aspirational; FR-595 (the `world_recall`
demotion) exists as the precedent; and FR-596 is **Enforced — Gate-1 KILL** with a
`## Gate-1 Outcome` section recording exactly the "numbers lie" root cause this FR
cites. Notably that finding surfaced *because* FR-596's GT-agent isolation +
throughline inspection (the FR-596 corrections) let the KILL be attributed to the
*ruler* rather than misread as a framing failure — the diagnosis chain is sound.

**Corrections required before enforce (do not widen scope):**

1. **State the binary exit condition that un-blocks the encoder on BOTH branches
   (PRIMARY — anti-deferral guard).** This is the *second* regenerability ruler, and
   it "blocks the protagonist-throughline encoder work." A ruler that measures a
   ruler must not become a standing excuse to never heal L7 (the `audit_as_ritual` /
   metric-fix-reflex trap, which this lineage is explicitly watching for). Make the
   resolution a one-shot corpus measurement with a declared two-way exit: **(a)** GT
   skeleton scores highly underdetermined (≥ ~0.70, thesis confirmed) → a *separate*
   demotion FR (the FR-595 analog) moves the gate, and the encoder work resumes
   against the new ruler; **(b)** GT scores low underdetermined (thesis refuted) →
   `affect_recall` stands and the encoder work resumes against its original ≥ 0.50
   gate. Either branch un-blocks the encoder — the ruler resolves the gate question,
   it does not indefinitely pause the layer.

2. **Carry the witness on the DETERMINISTIC channel, not the noisy judge alone
   (secondary).** The detective `betrayal → Hagen` vs `guilt → Pell` known-positive is
   the right witness, but AC currently lets it be satisfied by `[UNDERDETERMINED]`
   *or* a fidelity-judge `inverted`/`missing` entry. Require the **deterministic
   `[UNDERDETERMINED]` marker** on that beat as the primary assertion, with the
   temp-0.7 fidelity entry as corroboration only — otherwise the load-bearing witness
   is a flaky single LLM draw (the FR-594 deterministic-vs-noisy separation).

3. **Report the GT under-determination as a corpus-POOLED count, not a mean of
   per-genre ratios (L7-specific sparsity).** The affect skeleton is 5–8 deltas over
   ~5–6 affect-bearing beats per genre — a denominator of ~6, where one marker flip
   swings a genre ratio by ~17 points. At L5 the denominator was dozens of
   predicates; here per-genre N is too small to interpret and a mean-of-ratios
   over-weights the tiniest genre. Pool: total underdetermined / total affect-beats
   across all five genres for the headline number (the `gate_underpowered_for_its_margin`
   lesson applied to the diagnostic read itself).

4. **Treat the affect fidelity judge as MORE advisory than L5's (note, not a code
   change).** L5 fidelity judged *event* recovery; L7 fidelity judges *emotional*
   content (right kind/target/feeling), which is materially more subjective for an
   LLM judge. Lean the thesis on the deterministic simulability axis; the fidelity
   judge informs attribution but does not carry the verdict. Reinforces the
   diagnostic-only stance.

**Minor:** render both our L7 and the GT skeleton with the **same roster** (parity,
as the FR states); REQ-YG-020 reuse with no new CAP; tools `plot_modeller`-local
(OQ#4); diary + changelog `req: REQ-YG-020` — all correct, endorse.

**Frozen scope:** the `l7_measure.yaml` graph (node-for-node mirror of `l5_measure`),
the three pure tools (`render_l7_affect`/`score_affect_simulability`/
`combine_l7_measure`), the two new prompts (`regenerate_affect_arc`,
`judge_affect_fidelity`), and `--mode measure-l7` over the corpus on BOTH our
encoder and the GT skeleton. `l7_measure` is **diagnostic only** — `affect_recall`
stays primary, no gating is wired, FR-578/FR-596 are **not** re-litigated under it,
and the measurement resolves to one of the two declared exits. Demotion and gating
are a separate future FR.

## Problem

`affect_recall` compares our per-beat `eff_affect` deltas (op/char/kind/toward)
against a ground-truth affect skeleton. The FR-596 Gate-1 evidence (2026-06-25,
claude-haiku-4-5, all 5 genres) showed this target is structurally the wrong ruler,
in two ways `affect_recall` conflates:

1. **Under-determined target (the headline).** Hand-comparison of the detective output
   against GT, *restricting to the protagonist alone*, showed the model narrated a
   coherent alternative reading — `guilt → Pell` (empathy toward the witness she
   protects) — where GT encodes `betrayal → Hagen` (her moral relation to the
   antagonist). **Both readings regenerate the same beats.** The sparse skeleton cannot
   distinguish them, so `affect_recall` penalizes a narratively valid second reading.

2. **Radical sparsity (why it is *worse* than L5).** The GT affect skeleton is uniformly
   mono-protagonist and tiny — 5–8 deltas over ~3–4 matched `open…close` arcs on one
   character, across all five genres:

   | Genre | beats | beats w/ affect | deltas | protagonist | relational |
   |---|---|---|---|---|---|
   | detective | 9 | 6 | 8 | Marren | 2/8 |
   | historical | 10 | 6 | 6 | Naima | 2/6 |
   | horror | 7 | 5 | 5 | Brynn | 2/5 |
   | quest | 9 | 5 | 6 | Eira | 2/6 |
   | scifi | 13 | 6 | 8 | Mara | 3/8 |

   An ~8-token emotional skeleton is *far* sparser than L5's world-state (dozens of
   `at`/`rel`/belief predicates) and encodes interior states with no unique grounding
   in prose. FR-594 found the *denser* L5 GT skeleton already scored up to 1.00
   underdetermined (could not regenerate its own stories). The prediction here: the
   L7 affect skeleton is **more** underdetermined still.

The honest test is the FR-594 test, ported: feed the GT's own affect skeleton back,
ask the model to regenerate the emotional throughline, and measure how much it must
flag `[UNDERDETERMINED]`. If GT cannot regenerate its own emotional arc, `affect_recall`
is measuring the wrong thing — and the L7 gate must move before encoder work resumes.

## Proposed Solution

A YAMLGraph graph `examples/plot_modeller/graphs/l7_measure.yaml` that takes one
story's L7 affect encoding + roster + synopsis and produces an `l7_measure` record,
mirroring `l5_measure.yaml` node-for-node.

### State

```
state:
  genre:            str    # input
  roster:           str    # input (agent names)
  affect_skeleton:  str    # rendered per-beat affect delta stream (from load node)
  synopsis:         str    # input (source text)
  regen_arc:        str    # llm output — regenerated emotional throughline prose
  simulability:     dict   # deterministic score (GT-free)
  fidelity:         dict   # judge output
  l7_measure:       dict   # combined verdict
```

### Nodes

1. `render_affect` (python tool `render_l7_affect`) — load an L7 affect yaml (or GT
   `functions[].eff_affect`) + roster, produce the `affect_skeleton` delta stream
   (`<beat>: <op> <char> <kind>[ → <toward>]`). Pure, deterministic, unit-tested in
   `nodes/tools.py`.
2. `regenerate` (llm, new prompt `regenerate_affect_arc`) → `regen_arc`. Narrates one
   short emotional paragraph per affect-bearing beat from the deltas alone; flags
   `[UNDERDETERMINED: <what is missing>]` when a delta cannot be made into a felt,
   scene-grounded emotional moment (the analog of `regenerate_chapter`'s HARD RULES).
3. `score_simulability` (python tool `score_affect_simulability`) → deterministic
   count of `[UNDERDETERMINED]` markers / affect-bearing beats from `regen_arc`;
   emits `{underdetermined, beats, ratio}`. No LLM, no GT. *Lower = more regenerable.*
4. `judge_fidelity` (llm, new prompt `judge_affect_fidelity`, inline schema) — compares
   `regen_arc` against `synopsis`; emits
   `{recovered: list[str], missing: list[str], inverted: list[str], score: float}`,
   where `inverted` captures emotionally-wrong reconstructions (e.g. a kind/toward that
   reverses the source's actual feeling).
5. `verdict` (python tool `combine_l7_measure`) → merges (3) and (4) into
   `l7_measure = {simulability_ratio, fidelity_score, inverted_count, verdict}`,
   keeping the two axes orthogonal and attributable (never one opaque scalar).

### Edges

`START → render_affect → regenerate → score_simulability → judge_fidelity → verdict → END`
(linear; no loops — identical shape to `l5_measure.yaml`).

### Runner

Extend `run.py` with `--mode measure-l7` that runs the graph per genre over the corpus
and writes `results/evaluation/<genre>-l7-measure.yaml` plus an `l7-measure-summary.yaml`
(**corpus-pooled** simulability ratio — total markers / total affect-beats, per
Judgement C3 — plus mean fidelity and inverted count), mirroring the L5 measure
summary shape. Each genre measured on BOTH our encoder's L7 (`results/l7/<genre>.yaml`)
and the GT affect skeleton (`functions[].eff_affect`).

## Acceptance Criteria

- [ ] `graphs/l7_measure.yaml` lints clean (`yamlgraph graph lint`).
- [ ] `render_l7_affect`, `score_affect_simulability`, `combine_l7_measure` are pure
      python tools in `nodes/tools.py` with `@pytest.mark.req("REQ-YG-020")` unit tests
      (deterministic; no LLM).
- [ ] `prompts/regenerate_affect_arc.yaml` and `prompts/judge_affect_fidelity.yaml`
      exist; the latter has an inline schema (`recovered/missing/inverted/score`).
- [ ] `run.py --mode measure-l7` produces per-genre + summary YAML for all 5 genres
      against live LLM (log captured under `logs/`).
- [ ] **Witness the under-determination on the DETERMINISTIC channel (Judgement C2,
      PRIMARY).** Feeding the GT detective affect skeleton, the regenerated arc cannot
      uniquely recover `betrayal → Hagen` vs the equally-licensed `guilt → Pell`
      reading. The **load-bearing assertion is a deterministic `[UNDERDETERMINED]`
      marker on that beat**; a temp-0.7 fidelity-judge `inverted`/`missing` entry may
      corroborate but cannot stand in for it (the FR-594 deterministic-vs-noisy
      separation; `plausible_wrong_answer` cure).
- [ ] **Headline = corpus-POOLED under-determination, not a mean of ratios (Judgement
      C3).** Per-genre N is ~6 affect-beats, where one marker flip swings a genre ratio
      ~17 points. Report the headline as **total `[UNDERDETERMINED]` markers / total
      affect-bearing beats pooled across all five genres**, for BOTH our encoder's L7
      and the GT skeleton. The thesis is confirmed if the GT pooled ratio is **highly
      underdetermined (≥ ~0.70)**; a low GT ratio *refutes* the thesis and must be
      reported honestly.
- [ ] **Verdict is led by the deterministic simulability axis (Judgement C4).** The L7
      fidelity judge scores *emotional* content (more subjective than L5's event
      recovery), so `combine_l7_measure` leans the verdict on the deterministic
      simulability axis; the fidelity judge informs attribution only and never carries
      the verdict. The two axes stay orthogonal (never one opaque scalar).
- [ ] **Binary two-way exit that un-blocks the encoder on BOTH branches (Judgement C1,
      anti-deferral guard).** The measurement is a one-shot corpus resolution with a
      declared two-way exit — it resolves the gate question, it does not indefinitely
      pause L7:
      - **(a) GT pooled ratio ≥ ~0.70 (thesis confirmed)** → a *separate* demotion FR
        (the FR-595 analog) moves the L7 gate, and the protagonist-throughline encoder
        work resumes **against the new ruler**.
      - **(b) GT pooled ratio low (thesis refuted)** → `affect_recall` stands, and the
        encoder work resumes **against its original ≥ 0.50 gate**.
      The FR's Outcome section must record which branch fired and the un-block it
      authorizes.
- [ ] `l7_measure` is **diagnostic only**: `affect_recall` stays the primary FR-578
      gate, no gating is wired on the new measure, and FR-578/FR-596 are **not**
      re-litigated under it.
- [ ] Diary reflection added; changelog fragment added (`type: feat, scope:
      plot-modeller, req: REQ-YG-020`).

## Open Questions

1. **PRIMARY — does GT affect regenerate its own arc?** The whole FR rides on the
   prediction that it does not (≥ L5's underdetermined ratio). If GT scores *low*
   underdetermined, the thesis is refuted and `affect_recall` is **not** demoted —
   report and stop. (This is the Red-Hat premise check FR-594's Judgement demanded.)
2. **Simulability vs fidelity weighting.** Keep both axes separate and advisory this
   cycle (FR-594 lesson: the deterministic simulability axis and the noisy temp-0.7
   fidelity judge have different epistemic status; never collapse them).
3. **Power before gate.** Before any future FR lets `l7_measure` gate, declare a
   minimum-detectable-effect and required n for the fidelity axis (the simulability
   axis is deterministic and needs none). Until then, fidelity is advisory.
4. **Tool locality.** Keep the three pure tools `plot_modeller`-local in `nodes/tools.py`
   until a second consumer appears (YAGNI); reuse REQ-YG-020, no new CAP.

## Related

- FR-594 — the L5 regenerability measurement graph this FR ports node-for-node.
- FR-595 — the L5 `world_recall` demotion this FR's likely outcome mirrors for L7.
- FR-596 — the Gate-1 manual inspection ("numbers lie") that produced this FR's
  corrected root cause and indicated this ruler as the *first* next move.
- FR-578 — the monolithic L7 baseline whose `affect_recall` gate this measure tests.
- FR-579 — the merge node blocked on L7; reframed by this FR (gate may move).
