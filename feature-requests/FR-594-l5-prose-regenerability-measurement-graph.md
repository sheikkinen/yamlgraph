# Feature Request: L5 Prose-Regenerability Measurement Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — Authority GRANTED (2026-06-25)
**Effort:** 1–2 days
**Requested:** 2026-06-25

## Summary

Graduate the throwaway `spike_regenerate_prose.py` probe into a proper YAMLGraph
graph that measures an L5 encoding by whether its chapter prose is **regenerable
from the data alone**. The graph emits a two-axis measurement — *simulability*
(does the state machine license its own narration?) and *fidelity* (does that
narration match the source synopsis?) — replacing `world_recall`-vs-ground-truth
as the primary L5 quality signal.

## Value Statement

L5 authors get a GT-free, falsifiable ruler for "did the encoding capture the
story?" instead of `world_recall`, which (proven below) scores agreement with a
lossy skeleton rather than story capture.

## Judgement (2026-06-25)

**Verdict: Authority GRANTED — to build the ruler, NOT to swing it.** The technical
plan is clean and its artifacts are real: `spike_regenerate_prose.py` holds
`_render_beats`/`_fact`/`_render_world`/`_regenerate` (the functions to extract),
it reuses `prompts/regenerate_chapter.yaml` unchanged, `docs/L5-goals.md` exists,
and `nodes/tools.py` has none of the three proposed pure tools yet (confirming
they are new). The graph shape — plain `state:` keys, `type: python` tools with
`tool:`+`state_key:`, one `llm` node with an inline schema, a linear edge chain —
is all valid YAMLGraph. The diagnosis is also genuinely important: a probe finding
that the **ground-truth** L5 channel cannot regenerate its own stories
(detective 1.00, scifi 1.00 underdetermined) while ours can (0.11, 0.15) is a real
indictment of `world_recall` as a quality target, and it survives the one confound
I checked — GT regen is *handed* `initial_state` while ours gets `""`, yet GT still
scored more underdetermined despite that head start.

**Red Hat — the unchallenged premise this FR rides on.** If `world_recall` is
"structurally wrong," then FR-591/592/593 were all KILLed against a lossy skeleton.
That reframe is the FR's strength *and* its hazard: a single-run, temp-0.7,
claude-haiku-4-5 probe is being used to demote the only GT-anchored ruler the arc
has. The replacement is GT-free (good — measures story capture, not skeleton
agreement) but introduces an **LLM fidelity judge at temp 0.7** — the same noise
source whose single-draw cells I have flagged across FR-587/590/592/593 — and the
FR's own scifi finding (fluent-but-wrong, inverted climax) proves simulability
alone is gameable by confident drift. So the new ruler is not yet more trustworthy
than the old one; it is differently fallible. Grant builds it; grant does **not**
let it gate, and does **not** re-open the vocab arc.

**Corrections required before enforce (do not widen scope):**

1. **`l5_measure` ships as a DIAGNOSTIC; `world_recall` stays primary this cycle
   (resolve Open Question #1 — PRIMARY).** The FR's lean ("keep both one cycle, then
   demote") becomes a hard constraint: the `verdict` node reports, it does not block,
   and nothing in `run.py` is rewired to gate on `l5_measure`. Demotion of
   `world_recall` is a *separate future FR* once `l5_measure` has corpus history.

2. **Witness the fidelity judge against the labeled scifi inversion (PRIMARY).** The
   probe already found scifi's regen inverted the climax — that is a known-positive,
   so make it a test, not a promise: an acceptance criterion requires the fidelity
   judge to return **non-empty `inverted`** on the scifi case. Without this the judge
   is "trust me"; with it, it is the one thing that separates this ruler from
   rewarding fluent drift (the `plausible_wrong_answer` cure — assert beyond shape).
   This is the single most important correction.

3. **Keep the two axes orthogonal and attributable (FR-590 lesson).** `verdict` must
   encode *which* axis fired — low-simulability vs low-fidelity vs inverted — and
   never collapse to one opaque scalar. The simulability axis is deterministic
   (no LLM, no GT) and the fidelity axis is the noisy one; their epistemic status
   differs and the record must preserve that separation so a future fail is
   diagnosable, not just observed.

4. **Power before gate (resolve Open Question #2).** Before `l5_measure` is ever
   permitted to gate (a later FR), declare a minimum-detectable-effect and required
   n for the **fidelity** axis; the simulability axis needs no n (deterministic).
   Until then, fidelity is advisory. State this in the FR so the next author cannot
   silently promote a single-draw cell to a gate.

5. **Record the `initial_state` asymmetry, do not "fix" it.** `render_l5_beats` /
   the runner should note that GT renders with its `initial_world` and ours with
   `""` — kept for parity with the probe. It does not threaten the headline (GT is
   more underdetermined *despite* the advantage), but an undocumented asymmetry will
   read as a bug to the next reader.

**Minor:** Open Question #3 — keep the render/score/combine tools `plot_modeller`-local
in `nodes/tools.py` until a second consumer appears (YAGNI). Pin **REQ-YG-020** for
the pure-tool unit tests (reuse, as in the prior plot_modeller FRs); changelog
fragment + diary are already in the ACs — endorse.

**Frozen scope:** extract `_render_beats`/`_fact` into pure `render_l5_beats`;
add deterministic `score_simulability` and `combine_l5_measure`; add the
`judge_fidelity` prompt+schema (witnessed against scifi inversion); wire the linear
`l5_measure.yaml` graph and a `--mode measure-l5` runner emitting per-genre +
summary YAML; retire the spike on parity. `l5_measure` is **diagnostic only** this
cycle — `world_recall` remains primary, no gating is wired, and FR-591/592/593 are
**not** re-litigated under the new ruler. Metric demotion and gating are out of scope.

## Problem

`world_recall` measures token overlap between our L5 predicates and a
ground-truth L5 encoding. A prose-regeneration probe (2026-06-25, all 5 genres,
claude-haiku-4-5) showed this target is structurally wrong:

| Genre | GT-L5 underdetermined/beats | Our-L5 underdetermined/beats |
|---|---|---|
| detective | 8/8 = 1.00 | 1/9 = 0.11 |
| historical | 7/10 = 0.70 | 1/10 = 0.10 |
| horror | 4/7 = 0.57 | 3/7 = 0.43 |
| quest | 4/8 = 0.50 | 2/8 = 0.25 |
| scifi | 12/12 = 1.00 | 2/13 = 0.15 |

The ground-truth L5 predicate channel **cannot regenerate its own stories** — it
licenses near-zero narration without its glosses. So `world_recall` penalizes
our encoder for emitting the concrete `at/holds/rel` transitions that actually
make the story regenerable. Two failure modes the probe distinguishes that
`world_recall` conflates:

- **Lossy target** (GT-L5 unregenerable) → metric measures the wrong thing.
- **Fluent-but-wrong** (scifi: our regen inverted the climax) → high
  simulability, low fidelity. `world_recall` cannot see this; a fidelity judge can.

The probe currently lives in a spike with hardcoded rendering and a grep on a
`COVERAGE:` line. It must become a declarative, reusable graph to be a gate.

## Proposed Solution

A YAMLGraph graph `examples/plot_modeller/graphs/l5_measure.yaml` that takes one
story's L5 encoding + roster + synopsis and produces an `l5_measure` record.

### State

```
state:
  genre:          str          # input
  roster:         str          # input (agent names)
  initial_state:  str          # input, optional (GT initial_world; "" for ours)
  beats:          str          # rendered predicate stream (from load node)
  synopsis:       str          # input (source text)
  regen_prose:    str          # llm output
  simulability:   dict         # deterministic score
  fidelity:       dict         # judge output
  l5_measure:     dict         # combined verdict
```

### Nodes

1. `render_beats` (python tool `render_l5_beats`) — load an L5 yaml + GT roster,
   produce the `beats` predicate stream. Moves `_render_beats`/`_fact` out of the
   spike into `nodes/tools.py` (pure, deterministic, unit-tested).
2. `regenerate` (llm, prompt `regenerate_chapter`) → `regen_prose`. Reuses the
   existing prompt unchanged.
3. `score_simulability` (python tool `score_simulability`) → deterministic count
   of `[UNDERDETERMINED]` markers and beats from `regen_prose`; emits
   `{underdetermined, beats, ratio}`. No LLM, no GT.
4. `judge_fidelity` (llm, new prompt `judge_fidelity`, inline schema) — compares
   `regen_prose` against `synopsis`; emits
   `{recovered: list[str], missing: list[str], inverted: list[str], score: float}`.
5. `verdict` (python tool `combine_l5_measure`) → merges (3) and (4) into
   `l5_measure = {simulability_ratio, fidelity_score, inverted_count, verdict}`.

### Edges

`START → render_beats → regenerate → score_simulability → judge_fidelity → verdict → END`
(linear; no loops).

### Runner

Extend `run.py` with a `--mode measure-l5` that runs the graph per genre over the
corpus and writes `results/evaluation/<genre>-l5-measure.yaml` plus an
`l5-measure-summary.yaml` (mean simulability ratio, mean fidelity, inverted
count) — mirroring the existing eval summary shape.

## Acceptance Criteria

- [x] `graphs/l5_measure.yaml` lints clean (`yamlgraph graph lint`): 0 errors,
      1 warning (W026 fusion advisory on `judge_fidelity` — empirically refuted
      by the acceptance run, see below).
- [x] `render_l5_beats`, `score_simulability`, `combine_l5_measure` are pure
      python tools in `nodes/tools.py` with `@pytest.mark.req("REQ-YG-020")` unit
      tests (11 tests, deterministic; no LLM). `logs/fr594-green2.log`.
- [x] `prompts/judge_fidelity.yaml` exists with an inline schema
      (`recovered/missing/inverted/score`).
- [x] `run.py --mode measure-l5` produces per-genre + summary YAML for all 5
      genres against live LLM. `logs/fr594-acceptance.log`.
- [x] The graph reproduces the spike's corpus discrimination (ours ≪ GT on
      underdetermined ratio): **ours 0.313 ≪ gt 0.697** at corpus level.
- [x] `spike_regenerate_prose.py` retired (deleted): the graph reproduces its
      discrimination; the probe's logic lives in `l5_measure.yaml` + the three
      pure tools.
- [x] Diary reflection added; changelog fragment added.

## Acceptance Run (2026-06-25, claude-haiku-4-5, temp 0.7)

Full corpus: `run.py --mode measure-l5`. Each genre measured on BOTH our
encoder's L5 (`results/l5/<genre>.yaml`, `initial_state=""`) and the ground-truth
functions (`pre_world`/`eff_world`, `initial_state` = rendered `initial_world`).
Simulability = `[UNDERDETERMINED]` markers / beat count (deterministic, GT-free,
*lower = more regenerable*). Fidelity = LLM judge score; `inverted` = source
events whose meaning the regen reversed.

| Genre | ours sim | gt sim | ours fid | gt fid | ours inv | gt inv |
|-------|---------:|-------:|---------:|-------:|---------:|-------:|
| detective-thriller | 0.11 (1/9)  | 0.89 (8/9)  | 0.35 | 0.28 | 2 | 2 |
| historical-fiction | 0.40 (4/10) | 0.70 (7/10) | 0.28 | 0.25 | 2 | 0 |
| horror-survival    | 0.29 (2/7)  | 0.57 (4/7)  | 0.28 | 0.62 | 1 | 3 |
| quest-adventure    | 0.00 (0/9)  | 0.56 (5/9)  | 0.28 | 0.32 | 2 | 2 |
| scifi-hybrid       | 0.77 (10/13)| 0.77 (10/13)| 0.28 | 0.15 | **5** | 5 |
| **corpus mean**    | **0.313**   | **0.697**   | 0.294 | 0.324 | 12 | 12 |

**Verdict on the Judgement's corrections:**

1. **Discrimination reproduced (AC).** Corpus simulability ours 0.313 ≪ gt 0.697.
   4/5 genres show a clear gap; scifi ties at 0.77 (the known-noisy genre — a
   single-genre re-run earlier the same session gave ours 1.00, evidence of the
   regenerator's temp-0.7 marker variance, *not* the deterministic counter).
2. **Scifi inversion witnessed (correction #2 — the single most important AC).**
   `inverted` is **non-empty (5)** on scifi-ours. Across the corpus the judge
   fired inversions on every genre (12 total). The W026 fusion warning — that a
   4-field judge prompt might starve `inverted` — is **empirically refuted**; the
   prompt does not need the FR-585 discrimination/bookkeeping split this cycle.
3. **Axes stay orthogonal & attributable (correction #3).** `concerns` names
   which axis fired (`low_simulability` / `fidelity_inverted` / `low_fidelity`),
   never a single averaged scalar. e.g. historical-gt fired `low_simulability`
   only (fidelity clean), historical-ours fired `fidelity_inverted` only
   (simulable but drifted) — the two axes diverge, proving they measure
   different things.
4. **Underpowered for a gate (correction #4).** The fidelity/simulability *LLM*
   axes are noisy: scifi-ours simulability swung 1.00 → 0.77 across two runs with
   identical inputs. The deterministic counter is faithful; the variance lives in
   the regenerator's propensity to emit markers. A minimum-detectable-effect and
   required n MUST be declared before this gates anything. Ships **diagnostic
   only**; `world_recall` remains primary this cycle.
5. **initial_state asymmetry recorded (correction #5).** GT renders with its
   `initial_world`; ours renders with `""` (our encoder emits no initial world).
   This is documented in `run.py::_render_world_facts`, kept (not "fixed") for
   parity with the original probe.

## Power Analysis — loop closed (2026-06-25, claude-haiku-4-5)

Correction #4 demanded a minimum-detectable-effect and required *n* before this
ruler may gate. The corpus runner was executed **5× over all genres**
(`logs/fr594-power/`, aggregator `tmp/fr594_power.py`):

| Quantity | ours | gt | note |
|----------|-----:|---:|------|
| corpus-mean simulability — runs | 0.296 / 0.238 / 0.248 / 0.252 / 0.441 | 0.640 / 0.569 / 0.638 / 0.578 / 0.735 | |
| corpus-mean simulability — mean ± sd | **0.295 ± 0.085** | **0.632 ± 0.066** | absolute value is noisy (CV 29%) |
| corpus-mean fidelity — mean ± sd | 0.335 ± 0.023 | 0.358 ± 0.057 | **ours ≈ gt → fidelity does NOT discriminate** |
| total inverted — mean ± sd | 11.6 ± 1.67 | 6.2 ± 0.84 | ours drifts *more* (honest tension) |

**The signal is the paired GT-anchored discrimination, and it is robust:**

```
gap (gt_sim − ours_sim) per run:  0.344  0.331  0.390  0.326  0.294
mean gap = 0.337   sd = 0.035   se = 0.0156   t(4) = 21.6   (p ≪ 0.01)
```

Every run, without exception, scores ours more regenerable than the GT skeleton.
This is the well-powered gate: **ours simulability must be robustly below gt
simulability** (our L5 licenses more of its own narration than the lossy GT
predicate channel does). It needs no large *n* — the paired margin (0.337) is
~9× its own sd.

**What is NOT gateable (the underpowered axes):**

- **Absolute single-run simulability thresholds.** Corpus-mean sd 0.085 ⇒ an
  absolute-threshold gate needs **n ≈ 6 runs for MDE 0.10, n ≈ 23 for MDE 0.05**.
  A bare-threshold gate at n=1 would flip between runs (ours ranged 0.238–0.441).
- **Per-genre verdicts.** Worst-cell sd = 0.22 (scifi swung 0.46–1.00). Per-genre
  gating is hopeless at any feasible *n* — only the corpus mean is stable.
- **Fidelity as a discriminator.** ours 0.335 ≈ gt 0.358 (overlapping at sd
  0.023/0.057). Fidelity is a within-encoding quality probe, not an ours-vs-gt
  signal — it stays **advisory**.

**Loop-closing conclusion:** the ruler may gate, but only as the *paired
GT-anchored simulability discrimination on the corpus mean*. `world_recall`
(which FR-594 falsified as scoring a lossy skeleton) is demoted to informational
in the L5 eval. The metric fix is carried in **FR-595** (this FR built and
powered the ruler; FR-595 swings it).

## Alternatives Considered

- **Keep it a spike.** Rejected: a measurement that gates L5 must be declarative,
  unit-tested, and reusable — not a hardcoded script with a grep.
- **Add fidelity to the existing `evaluate.py` world_recall scorer.** Rejected:
  conflates two orthogonal axes and keeps the GT-dependence the probe just
  falsified.
- **Simulability only (drop the fidelity judge).** Rejected: scifi proved
  fluent-but-wrong is real; without the judge the ruler rewards confident drift.

## Open Questions (for Judgement)

- Should `world_recall` be *demoted to diagnostic* in the same change, or left in
  place until `l5_measure` has corpus history? (Lean: keep both one cycle, then
  demote.) **RESOLVED:** demote now — carried in FR-595, evidenced by the power
  analysis above (the GT-anchored discrimination is robust at n=5, t=21.6).
- Fidelity judge variance: single-run temp 0.7 regen is noisy. Declare a
  minimum-detectable-effect + required n before this becomes a *gate* (carry the
  `gate_underpowered_for_its_margin` lesson from FR-593). **RESOLVED** by the
  Power Analysis section: gate on the paired GT-anchored simulability
  discrimination (corpus mean, robust at n=5); absolute thresholds need n≈6
  (MDE 0.10); per-genre and fidelity are not gateable.
- Does the rendering belong in `nodes/tools.py` (plot_modeller-local) or is it a
  reusable primitive worth a shared location? (Lean: local until a second
  consumer appears.)

## Related

- FR-593 — story-level vocabulary pre-stage; its corpus gate was inconclusive,
  which motivated questioning the target metric.
- FR-591/592 — oracle vocab tests that falsified the vocabulary hypothesis and
  pointed at the transition/precondition model.
- `examples/plot_modeller/docs/L5-goals.md` — the outsider-view reframing
  (simulability + downstream coherence as L5's true objectives).
- `examples/plot_modeller/graphs/l5_measure.yaml`,
  `prompts/regenerate_chapter.yaml`, `prompts/judge_fidelity.yaml`,
  `nodes/tools.py` (FR-594 section) — the graduated ruler that replaced the
  retired `spike_regenerate_prose.py` probe.
