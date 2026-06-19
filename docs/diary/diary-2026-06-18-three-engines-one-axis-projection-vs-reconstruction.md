# Three engines, one axis: the day the architecture named itself

**Date:** 2026-06-18
**Context:** After the 10026-BC calibration run, a hypothesis ("good turn generator,
shallow plot reconstructed from prose") was tested against all three story engines in the
repo. Output: `examples/dungeon_master/docs/continuity-projection-plan.md`.

## What happened

The user proposed a hypothesis as a sentence, not a task: *"we have a nice turn-by-turn
action generator, but we are trying to reconstruct the plot from shallow synopsis and turn
dialogue."* I had spent the prior turns hardening my recommendation around the FR-507/509/
510 cluster. The hypothesis reframed all of it: those FRs operate at the chapter-*open*
boundary, but the defect is born at chapter *close*, where an LLM reconstructs lifecycle
state by reading the prose it just wrote. The 10026-BC seam data proved it cold: ch7 prose
says Witta "vanished into the flood," ch7 `character_lifecycle` says `existence_state:
"alive"`. The generator wrote a clean death; the reconstructor mis-read it.

Then the user pointed me at two sibling engines -- `examples/ebook`, then
`examples/demos/novel_generator` -- and the design space resolved into a single axis:
**projection (plan -> prose) vs reconstruction (prose -> plan).**

## The trap I was in

**working_system_inertia at architectural scale.** DM v2's turn generator is genuinely
excellent -- the prose is vivid, the dialogue lands. That quality was *camouflage*: it made
the missing plot layer invisible, because every chapter read well in isolation. I kept
proposing patches to the seam (more gates, better extraction prompts) -- the
`downstream_fix` trap -- because the part that worked so well kept me from seeing that the
*direction of truth* was backwards. It took an outside hypothesis plus two comparison
engines to break the inertia. I could not see the water I was swimming in until shown two
other pools.

## The insight that crystallized

**Parallel-safety is the litmus test for projection.** This was the moment the abstraction
earned its keep. `novel_generator` fans prose across all beats with `type: map` --
simultaneously -- because plot truth lives in the authored timeline, not in any beat's
prose. `ebook` parallelizes 9 chapters by sharing *no* state. DM v2 *cannot* parallelize
chapters: each must wait to read the previous one's prose-derived `world_state`. **The
forced serial ordering is not an implementation detail -- it is the architectural
fingerprint of reconstruction.** If a fact has to be read back out of prose, the engine
cannot project it, and cannot parallelize on it. That single test ("could two chapters be
generated against this fact without reading each other?") now defines done for the fix.

## What each engine was right and wrong about

The synthesis only worked because no single engine was the answer:
- ebook: right that every generated artifact deserves a judge->amend gate; wrong that
  continuity is optional.
- novel_generator: right that prose is projected from an authored plan; wrong that the plan
  (`summary|characters|importance`) can carry a death.
- DM v2: right about the rich typed seam and turn-by-turn prose; wrong that the seam's
  load-bearing facts should be reconstructed from that prose.

The plan takes one virtue from each: project the lifecycle ledger (novel_generator),
authored richly enough to hold a death (DM v2's typed model), validated by a judge->amend
gate instead of re-extracted (ebook).

## Heuristic

**When a system can only run sequentially, ask whether the sequence encodes a real data
dependency or a reconstructed one.** A real dependency (B genuinely needs A's *output*) is
irreducible. A reconstructed dependency (B needs to *read back* a fact that A could have
*authored* up front) is an architecture smell: the fact is being inferred downstream
instead of projected upstream. Making it parallelizable is the same move as making it
correct -- both require authoring the fact before the prose, not after.

## Distinction worth keeping

A description of three engines is *inventory*; a statement of which axis they vary on, and
what that implies for the fix, is *analysis* (the `research_as_inventory` trap, avoided
here only because the user's hypothesis supplied the axis). The deliverable was never "what
do these examples do" -- it was "what is the one dimension they disagree on, and where does
DM v2 sit on it."

## Seed

The projection plan asserts lifecycle and resolved-conflict identity are the only facts
worth projecting. But a saga has more invariants -- possession, location, debts owed,
promises made. **Which story facts are worth the cost of projection, and which are cheap
enough to keep reconstructing?** Is there a principled threshold -- "project any fact whose
violation a reader would notice; reconstruct the rest" -- and does that threshold map
exactly onto the reviewer's reader-salient vs micro-state distinction from FR-532? If so,
the calibrated critic is not just a grader; it is the *specification of what to project.*
