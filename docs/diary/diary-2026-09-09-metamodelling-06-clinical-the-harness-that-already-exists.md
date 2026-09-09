# Clinical practice: the harness that already exists

**Date:** 2026-09-09
**Series:** metamodelling, part 6
**Trigger:** series continuation; the rung where the boundary is chosen by
harm, not by cost.
**Context:** clinical practice and its regulated software are the fields
with the most mature external harness of any in this series. They did not
get it from theory; they got it from incidents. The field is therefore
the best available picture of what a harness looks like after it has been
paid for, and what it costs to keep running.

## The field's harness

| Field practice | Framework triple | Note |
|---|---|---|
| Evidence grading (GRADE: meta-analysis → RCT → cohort → case series → expert opinion) | **the oracle-rung ladder, made explicit and stamped on the output** | recommendation strength is stated *with* the recommendation; the reader knows which rung it stands on |
| Guideline → evidence → recommendation | traceability | every recommendation points at its evidence and its rung |
| Risk management (ISO 14971), hazard analysis | pre-mortem, institutionalised | "what harm could this cause" is written before the design, and traced to mitigations |
| Software lifecycle (IEC 62304) | RTM with safety classification | requirement → design → verification, with class deciding rigour |
| Clinical decision support: interaction alert, dose-range check | PreToolUse hook | fires at the order, before the effect exists |
| Second signature, double-check | independent human at the action | for the highest-harm classes only |
| Incident reporting, morbidity and mortality review | diary → graduation | the field's learning loop; slow but real |
| Post-market surveillance | reality oracle, continuous | outcome data flows back to the harness |

## The boundary is chosen by irreversibility

Every previous part placed the hook at the cheapest boundary. This field
places it at the most *irreversible* one: the order, the prescription,
the administration. Cost is secondary. The interaction alert fires when
the order is entered because after administration there is no rollback,
and the alert's cost (a click, a second) is paid regardless of how
unlikely the harm is.

This is the correction to part 3's heuristic. The earliest boundary and
the cheapest rung are the right default when actions are reversible. When
they are not, the boundary is fixed by the point of no return and the
harness pays whatever the check costs there.

## Where the generator fails in this field

- **Plausible dosage.** A number in the right unit, the right order of
  magnitude, the right decimal shape, and wrong. Mechanical oracle
  exists: dose-range check per drug, per weight, per renal function.
- **Unit and name confusion.** mg / mcg; look-alike sound-alike drug
  names. The field already maintains lists; a hook consults them.
- **Guideline without rung.** A recommendation stated with the confidence
  of a meta-analysis and the evidence of an opinion. The field's harness
  requires the rung on the output; a generator omits it by default.
- **Population drift.** A correct recommendation for the wrong patient
  class: adult dosing for a child, a trial population that excluded the
  patient in front of you. Reference oracle: the guideline's inclusion
  criteria against the patient's record.

## Alert fatigue: the harness's own entropy

The field's most instructive finding is not about the generator. It is
that a hook that fires too often gets clicked through. Override rates
for interaction alerts are documented in the literature at very high
levels; the alert that always fires carries no information, and the one
that matters is dismissed with the same reflex as the ninety-nine that
did not.

This is `audit_as_ritual` with an outcome attached, and it is part 1's
seed — *the harness has no harness* — made concrete. A gate's health is
its override rate. A gate overridden nearly always is either wrong or
placed at the wrong boundary, and it is actively harmful because it
trains the operator to bypass. The field measures this; most software
harnesses do not.

## Table for the field

| Boundary | Oracle | Action |
|---|---|---|
| recommendation drafted | evidence rung stated | deny without rung |
| recommendation drafted | evidence cited resolves; population matches | flag mismatch |
| order entered | dose range, interaction, allergy (mechanical) | deny / require override reason |
| high-harm order | second signature | block until |
| administration | barcode match patient–drug–dose | deny |
| outcome | surveillance, incident report | amend the harness |
| any gate | **override rate** | retune or remove the gate |

## What the field returns to the framework

1. **State the rung on the output.** Part 1's rule 2 said "name the
   oracle"; this field says name it *to the reader*, on the artifact,
   every time. A claim without its rung is a claim wearing the top rung.
2. **Irreversibility fixes the boundary.** Cheapest-earliest is the
   default; point-of-no-return overrides it. Enumerate which actions have
   no rollback and put the hook there regardless of cost.
3. **Measure override rate.** Every deny needs a counter for how often
   it is bypassed. That counter is the harness's entropy metric, and a
   gate with a very high override rate is degrading the harness's other
   gates by training the reflex.
4. **Pre-mortem is a document, not a mood.** Hazard analysis is written,
   traced to mitigations, and reviewed. The framework's rule 7 (route
   failures to the harness) has a *forward* form: route imagined
   failures to the harness before they happen.

## Traps

**`gate_fatigue`.** A hook that fires so often it is bypassed by reflex.
Its presence lowers the value of every other hook.

**`rung_omitted`.** A recommendation without its evidence grade. Reads
as the strongest grade; is whatever it is.

## Heuristic

For every deny, keep the override count. For every irreversible action,
place a check at the action regardless of cost. For every claim, stamp
the rung it stands on.

**Seed:** `.github/hooks/logs/audit.jsonl` records denials. Does anything
compute the override rate per guard: how often a denial is followed by
the same action succeeding via another route? The field says that number
is the health of the harness, and the harness does not currently report
it.
