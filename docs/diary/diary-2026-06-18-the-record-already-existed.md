# The Record Already Existed

**Date:** 2026-06-18
**FR:** FR-521 (supersedes rejected FR-520)
**Arc:** DM v2 intra-chapter continuity hardening

## What happened

A reader watched Arnulf — swept down a flooded river and declared gone — keep
hauling himself onto the bank turn after turn. FR-519 had already added final-cut
enforcement, but 10022-BC proved a *clean final cut still leaves the break in the
chapter body*: the dead man acts at 23% through the chapter, in a running turn no
gate watched.

FR-520 was written and **gate-opened** to fix it: a new pure `positional_memory.py`
to *produce* a turn-grained record of who-is-where so the next turn could read it.
Then the user asked the question that killed the module: *"consider alternatives.
should this be the director's job?"*

It already was. The director emits a `continuity` judgement **every turn**. On
10022-BC Ch3 it flagged Arnulf on **8 of 16 turns**, verbatim and precise:
*"Arnulf acts after being swept away and disappeared; he cannot physically grab the
bank edge."* The record FR-520 proposed to build was already being written — and
thrown away. `running_scene` threaded the recaps forward but not the director's
flags, so the intent map regenerated blind, re-proposed the break, and the director
re-flagged it. The Scripture has a name for this: `detection_without_enforcement` —
"lint without gate = advisory." The defect was 12 lines of wiring, not a module.

## The trap

**`framework_costume` / new-module reflex.** FR-520 felt like the right size of fix
— a clean pure module, fully testable, a satisfying amount of code. The premise
("there is no turn-grained record") was never checked against what the director
*already does*. A gate-open judgement with five sub-amendments (B1–B5) had been
written on a **false B0**. The cure was not in the plan; it was in re-reading the
prompt the system already runs.

## The cure

Mark FR-520 rejected, replan as FR-521 = *feed the existing signal forward*.
`_continuity_constraints_block` unions the trailing 3-turn window's flags (J1: a
single clean turn must not drop a still-true constraint) and phrases them as a
constraint on **intent selection**, never narration (J4: so the forbidden text
cannot echo into the recap). Plus J2: `missing_presumed_dead` is a chapter-scoped
death-point in the warn-only lane — the exact lifecycle state the confirmed-only
filter excluded, the state Arnulf's whole presumed-dead→returns arc rides — while
the before-open bar stays confirmed-dead-only so his ch6 return is never barred.

S2 (drop a repeatedly-flagged actor from the roster) stayed **gated**: it needs a
structured offending-actor field the director does not yet emit, and no witness
demands it. Build the wiring; defer the module until a failure asks for it.

## Heuristic

Before building a component to *produce* a signal, grep the system for a component
that already *emits* it. A detector whose output is recorded and never read is not
missing detection — it is missing a wire. The cheapest continuity fix was not a new
module; it was reading the warning the director had been shouting into a closed
room for eight turns.

**Seed:** The director's flags are prose strings re-parsed downstream — the
prose→structured boundary J3 warns about. When does feeding a model its own prior
free-text judgement (the windowed flag block) become a liability rather than a fix —
does the carried constraint ever *teach* the break by naming it, and is the
intent-scoped framing (J4) actually enough to keep the negation from echoing?
