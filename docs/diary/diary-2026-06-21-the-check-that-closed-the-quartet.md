# The Check That Closed the Quartet

**Date:** 2026-06-21
**FR:** FR-562 (DM v3 M3 -- affect closure)

## What happened

The smoothest milestone of the v3 arc. Four pure narrative checks were always the plan
(lifecycle, grounding, antecedent, closure); M3 wrote the last one. `AffectDelta` had been carried
but inert since M1 -- the floodmark fixture dutifully opened `loss` and `guilt` and closed both, and
nothing read it. `_check_affect_closure` finally reads it: an ordered pop-walk over the same canonical
order the other three checks use, recording the opener of each affect unit and discharging it on
close. Residual opens become `unclosed_affect`, localized to the opening beat, unless the author lists
the unit in a new per-`(char, kind)` `intentional_open` allowlist.

RED landed four failures (dropped confrontation, intent suppression, close-then-reopen, report
ledger) and two passes (absence assertions that had to stay green). GREEN flipped all six. 450 DM
tests pass.

## Trap

**design_stub_as_contract.** The design doc's check-4 stub said the escape hatch was a plan-level
"intentional-open-ending" flag -- a single boolean. The judgement (J1) had already caught that a
global flag would exempt *every* open affect and gut the check, and approved the FR's per-unit
allowlist instead. The trap is subtle: the design stub *looks* authoritative, and a faithful
implementer would have built the boolean and shipped a check that any plot could trivially silence.
The stub was a sketch, not a contract; treating it as a contract would have produced compliant-but-
useless code.

## Cure

**reconcile_the_sketch.** When the implementation deliberately improves on a design sketch, edit the
sketch in the same diff (J1 fold). I updated the design doc's `_check_affect_closure` docstring to the
per-unit allowlist and the ordered-walk note, so the next reader inherits the corrected contract, not
the superseded boolean. This is the same move FR-561 made when enforcement found J5 was wrong: the
spec is cheap to fix and expensive to leave stale. A sketch that disagrees with the code is a future
regression waiting for a faithful implementer.

## Seed

Three of the four narrative checks now share an identical shape: order the functions once, walk them
recording producers/openers in a dict, emit a flaw for each residual keyed to the recording beat.
Should these collapse into a single parameterized "ledger check" (produce/discharge over an ordered
walk), or does the explicitness of three named functions buy more clarity than the abstraction would
save -- and where exactly is the line between honoring a pattern and over-abstracting it?
