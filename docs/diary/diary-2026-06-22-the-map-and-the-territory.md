# The map and the territory

**Date:** 2026-06-22
**FR:** FR-559–565 (v3 plot model arc, M0–M4b + producer integration)

## What happened

After enforcing M4b (realize) and FR-565 (producer integration), the full v3
plot plan arc is wired end-to-end. The natural next step was to read the four
documents that justified it — the research plan, two independent research
passes, and the ADR — and compare what was proposed against what was built.

The comparison revealed a pattern: the plan was deliberately more ambitious
than the build, and that gap is a feature, not a bug. Six SAT checks were
proposed; four shipped. Five lanes were ranked; three are active. The IPOCL
partial-order spine was specified with first-class causal links; the build
uses explicit author-declared ordering edges. The FR-557 turn engine was
supposed to be the realizer; the actual binding is a string merge into the
existing `instruction` field.

## The trap: plan fidelity as a virtue

The instinct after reading a detailed ADR is to measure the build against it
and treat every deviation as a gap to close. But the plan itself prescribed
"prototype first, falsification-gated" — it asked to be partially built and
evaluated, not faithfully transcribed. The deviations are not drift; they are
the plan working as intended.

The FR-557 realizer is the clearest case. The plan assumed the turn engine
would be extracted into a doc-free `TurnRequest`/`TurnResult` interface, and
the plot model would plug into it. Instead, the actual realize binding
(`beat_instruction → merge_beat_instruction`) found that the existing
`instruction: str` parameter was the right aperture. The plan's §7 is stale,
but the build is better — less coupling, no schema widening, leaf-pure.

## The insight: a plan is a hypothesis about the build, not a spec for it

The four documents form a chain: questions → research → decision → build spec.
Each narrows the space. But the build is a fifth document that talks back —
it discovers constraints the spec couldn't see (serialization boundaries,
import cycles, the string-aperture insight) and answers them by deviating.
The ADR's value is not in being followed but in having been written: it
forced the lane ranking, the falsification test, and the strangler-fig
posture that made the build safe to deviate within.

The two independent research passes converging on the same spine is genuine
evidence — not because they produced the right plan, but because they
constrained the space enough that the build could safely explore within it.

## Heuristic

**plan_as_hypothesis:** Treat an architectural plan as a hypothesis about the
build, not a specification of it. Measure the build against the plan's
*acceptance criteria* (do the observed break classes become unrepresentable?),
not its *proposed mechanism* (did we use FR-557's TurnRequest?). A build that
passes the criteria while deviating from the mechanism is a successful
experiment, not a failed implementation.

## Seed

The plan proposed 6 SAT checks; 4 shipped. The two missing checks (capped
reachability, causal threat resolution) require the full `unified-planning`
solver. But the four pure checks already cover the observed break classes.
Is there a premise in the existing corpus where the missing checks would have
caught a defect the pure checks missed? If not, the solver integration may
be permanently deferrable — a capability that exists in `up_model.py` and
`solve_status` but never needs to gate a real book.
