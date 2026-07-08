# The gate that fixes the world it judges — FR-692

*2026-07-08*

## What happened

FR-692 grows canon with antagonistic structure — kin who object, traders whose
interests cut across the truce — bounded by FR-691's plot threads. Two pure
gates carry the enforcement: **admission** (a new entity must cite the thread it
pressurizes) and **reciprocity** (a kinship edge must be acknowledged in
reverse). The reciprocity gate, run against real canon, condemned three
non-reciprocal edges the FR had predicted: Reinthilde names her mother and
father, but neither Hilde nor Gunnar named her back; Berno claims Gunnar as
clanmate, but Gunnar never claimed Berno.

## The trap: `downstream_fix` in the schema editor

Twice while adding the optional `pressurizes` field I let the `oldString`
swallow the *next class's declaration* (`class Event`, then `class Location`).
The field landed correctly but the class header vanished, and the failure
surfaced far downstream — a `NameError: name 'Location' is not defined` at
module-registration time, three classes below the edit. The symptom (an
undefined name in a dict literal) was nowhere near the cause (a dropped
`class` line). The cure was the boundary: read the *seam* between the field and
the next class, not just the field. When appending a trailing field to a
Pydantic model, the blast radius is the class boundary below it.

## The insight: a gate that repairs, not just reports

FR-691's gates only ever *judged* — they read `story/` and returned violations.
FR-692's reciprocity gate is different: its RED verdict on real canon is a
**work order**. The gate found the three missing edges; the fix was to add
exactly those three reverse edges, additively, and watch the same gate go green.
The condemning test (`test_reciprocity_holds_on_repaired_canon`) loads the four
kinship principals straight from canon — it passes trivially under the stub, but
under GREEN it *requires* the repair to exist. The test is both the condemnation
and the acceptance.

## The judgement I held: source canon is not `story/`

FR-691 ran its pipeline live and committed the regenerated `story/` artifacts —
cheap, because `story/` is derived and idempotently regenerable. FR-692's agent
would mutate *source* canon with LLM-invented entities. I froze the Judgement to
keep that run operator-driven: the deterministic core (schema + gates + the
three hand-verified repairs) is the CI-kept deliverable; the LLM world-building
is lint-clean wiring an operator invokes and reviews. `working_system_inertia`
would have had me run the agent because "FR-691 did" — but the blast radius is
different, and the enforceable value lives in the gates, not the generation.

## Seed

The reciprocity gate turns a validation into a work order — RED names the exact
edges to add. Which other gates in this codebase secretly encode their own fix,
and could emit a *patch* (the missing reverse edge, the absent sequence value)
alongside the violation, so the remediation is mechanical rather than
interpretive?
