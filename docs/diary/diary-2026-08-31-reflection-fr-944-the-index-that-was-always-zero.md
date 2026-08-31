# Reflection: FR-944 — the index that was always zero

**FR:** FR-944 map-to-map index attribution · **Date:** 2026-08-31

## What happened

FR-943's census containment went live and died in all four batches with
`duplicate finding for item index 0`. The investigation ended one `Counter`
away from the artifact: every one of 200 findings carried `_map_index: 0`.
The framework had been lying about row identity in chained maps since the
shape existed — and nothing ever noticed, because the census prompt
smuggled the true index through the LLM as `source_index`, and `sorted_add`
sorting all-zeros is indistinguishable from sorting nothing.

## The trap: a consumer-shaped hole in the test lattice

`MAP_TO_MAP` had classification tests (does the edge get named right?) but
zero runtime tests (does the compiled graph do the right thing?). The shape
was refactored twice (FR-066/067, FR-718) with its semantics "preserved
verbatim" — each refactor faithfully preserving a defect no test had ever
pinned. Preservation discipline is only as good as the witness set: a
faithfully preserved behavior with no runtime witness is a faithfully
preserved bug. Call it **verbatim_preservation_of_the_unwitnessed** — the
refactor's contract ("no behavior change") is vacuously satisfied when the
behavior was never observed.

## The cure that worked: probe before compiler

The LLM-free repro (two chained python-tool maps, 3 items) cost ~90 seconds
and turned a 200-haiku-call incident into a deterministic unit test. Then
the R-1 probe — expressing the candidate fix as an *explicit* pass-through
node in user YAML before writing any compiler code — proved the barrier
semantics on the unmodified framework. The fix then had nowhere to hide:
the compiler change just mechanizes a topology the probe already validated.
This is `test_before_reading` extended to fixes: if the cure can be
expressed as a graph topology, run the topology before compiling it in.

## The judge earned its fee

The judgement caught a real error in my FR: I claimed two research personas
supported the barrier join when they prescribed index threading. I had
laundered my own preference through the research record's authority
(`plausible_wrong_answer` at the citation level — the reference existed,
the content didn't match). It also forced the N×M independent-list witness
into the frozen matrix, which turned out to be the strongest test in the
suite: 6 sends where 2 belong is a louder condemnation than any index
sequence.

## Second witness note

The FR-767 pre-command guard denied two pure-read/pure-commit commands this
session because their *text* contained `graph.yaml` / `pytest ... | head`.
Second session in a row (FR-943 hit the same class). Guards that match
command text rather than command effect tax every innocent mention;
recurrence noted for graduation watch.

**Seed:** Which other synthetic-topology defects are hiding behind
shape-classification tests with no runtime witness? PARALLEL_FANOUT and
FROM_MAP with conditions have the same test lattice shape as MAP_TO_MAP
did — a one-day sweep writing one runtime witness per EdgeShape member
would either prove the lattice sound or find FR-944's siblings.
