# The context that loses the inventory

**Date:** 2026-06-19
**Context:** A meta-reflection prompted by a recurring smell across the DM v2 arc. Three
times now the working context has failed to recall things that already exist in the very
repo it is editing:

1. At the examples/demo level, we did not know several other novella-adjacent tools
   already existed — `examples/book_reviewer`, `examples/book_translator`,
   `examples/ebook`, `examples/storyboard` all coexist with `examples/dungeon_master`,
   and the DM example itself carries a whole `scripts/` shelf
   (`witness_book_compose.py`, `continuity_report.py`, `scan_beat_gaps.py`, ...).
2. The existence of `book_reviewer` was lost a while ago and had to be rediscovered.
3. This session, we nearly re-derived a "chapter regenerator" from scratch before
   recalling that FR-522 already shipped one: `api/chapter_replay.py::replay_chapter`
   with a CLI front at `scripts/replay_chapter_continuity.py`. The spike only worked
   because we *happened* to find it.

## The trap

This is not forgetfulness in the human sense — it is **structural blindness to inventory**.
My context window holds the *task* vividly and the *codebase* dimly. I carry forward what I
just wrote and what I was just told, but I do not carry a map of what already exists. So my
default posture toward "we need X" is *build X*, not *find X*. The Scripture already names a
cousin of this — `research_as_inventory` (mistaking description for analysis) and
`false_duplicate` (syntactic similarity hiding semantic difference) — but this is the
inverse failure: **semantic need without syntactic recall.** I needed a chapter regenerator;
one existed under a name (`replay`) my keyword instinct (`regen`) would never have grepped.

The cost is asymmetric and quiet. When I re-derive something that exists, nothing fails
loudly. The new code works. The tests pass. The duplicate sits beside the original, and the
two drift apart until one of them carries a bug-fix the other lacks. `book_reviewer` was not
lost with a crash; it was lost by *absence* — it simply stopped being mentioned, and
absence leaves no stack trace. This is the `inventory_by_visibility` trap from the asset-
inventory diary, seen from the other side: there I over-ranked legible code; here I cannot
*see* code at all unless something drags it into context.

## Why naming defeats grep

The chapter regenerator near-miss is the sharpest lesson. The capability is "regenerate one
chapter"; the artifact is named `replay`. Keyword search is a thesaurus-poor instrument —
it finds the word, not the function. An agent that searches by the word it would have
*chosen* will systematically miss artifacts named by the word someone *else* chose. The cure
is not better grep; it is an inventory indexed by **capability**, not by **token**. We have
exactly this machinery already — the `capabilities/CAP-*.yaml` registry — but it indexes
framework capabilities, not example/demo tools. The demo layer has no manifest, so it has no
memory.

## Reflection on the process

The deeper issue is that *research-first* (Commandment 1) is enforced for the framework but
not for the example surface. Before touching framework code I am steered to CAPs, REQs, and
the module map (`reference/module-map.md`). Before touching `examples/dungeon_master` I have
no equivalent — no "here is what already lives here." So the same agent that would never
re-implement a node factory cheerfully re-implements a chapter replayer, because the demo
layer was never given the enforcement scaffolding the core layer has. The blindness is not a
property of the model; it is a property of *which surfaces we instrumented*.

## Questions we need to ask

Before building anything at the example/demo level, the process should force these:

1. **"Who already solved this here?"** Not "does a function named X exist" but "does a
   *capability* matching this need exist under any name?" — searched against a capability
   index, not a token grep.
2. **"What is the inventory of this directory?"** Is there a manifest of the tools,
   scripts, and entry points in `examples/<name>/` that I can read in one shot, the way I
   read `module-map.md` for the framework?
3. **"What synonyms would someone else have used?"** Before grepping `regen`, also grep
   `replay`, `rebuild`, `redo`, `reoutline`, `recompose`. Name the concept three ways and
   search all three.
4. **"When did this last get mentioned?"** Absence-by-attrition (book_reviewer) is invisible
   unless we ask. A tool unmentioned for N sessions is a tool at risk of being re-derived.
5. **"Should this be a manifest entry?"** When I *do* build something new at the demo level,
   does it get registered somewhere a future context will look — or am I adding to the very
   pile that the next session will fail to inventory?

## Heuristic

**Context carries the task brightly and the inventory dimly; treat "build it" as a
hypothesis to be disproven by inventory, not a default to act on.** For any "we need X" at
the example/demo level, the first move is an inventory pass — capability-indexed, multi-
synonym — *before* the first line of new code. An agent's recall of what exists is not a
fact about the codebase; it is a fact about what fell into its context, and that set is
small, recent, and biased toward what it authored. The codebase is always larger than the
context's memory of it.

## Seed

The framework has `capabilities/CAP-*.yaml` and `reference/module-map.md` as its inventory
of record; the example/demo layer has nothing. **What would a `examples/INVENTORY.md` (or a
generated `examples/<name>/MANIFEST.md`) cost, and could it be auto-generated from
docstrings + script `__main__` blocks the way the module map is — so that "what already
lives here" is one read away, indexed by capability and not by the name its author happened
to pick?** And the sharper version: should the demo layer inherit the same research-first
gate the framework has, so that adding a new `examples/*/scripts/*.py` is *blocked* until
the author has cited the inventory they searched?
