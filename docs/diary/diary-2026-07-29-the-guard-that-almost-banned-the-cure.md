# The Guard That Almost Banned the Cure

**Date:** 2026-07-29
**Context:** FR-765 round 2 — wrapping graph authoring as an executable
copilot-node adapter (judge-fr shape) after round 1 shipped it as
documentation only.

## The trap: re-entry guards copied verbatim inherit the wrong scope

My amended FR copied the judge-fr re-entry guard almost word for word:
the launched agent "must never re-invoke the skill/adapter/yamlgraph."
For a judge, that is correct — a judge has no legitimate reason to run
yamlgraph at all. For an *author*, the same sentence is self-refuting:
the doctrine's own acceptance criteria REQUIRE the launched agent to run
`yamlgraph graph lint` and a smoke command against the graphs it
authors. A verbatim guard would have produced an agent contractually
forbidden from performing its mandatory validation step.

The round-2 judge caught this as R-1 before any code existed — the
cheapest kill rung again (`spec_kill`). The cure was to narrow the ban
to *recursion into the route* (the skill, the wrapper, the adapter
graph) while explicitly stating that ordinary validation of authored
targets stays required. The prompt now says both things in the same
breath, because an instruction that only bans is read broadly by the
next model.

Heuristic: **a guard transplanted between roles must be re-scoped to
the new role's duties — ban the recursion, not the profession.** The
judge and the author both live inside copilot-node adapters, but the
judge's tools are read-and-write-verdict while the author's tools
include the very CLI the guard named. Same shape, different closure.

## Second observation: the FR-756 gate and the honest dodge

The adapter tests read committed files and run zero processes, yet the
FR-756 module gate pattern-matches literal boundary strings in test
source. Round 1 reworded a docstring; round 2 constructs paths from
`Path()` parts with a comment explaining why. This is now twice that
the same gate has been satisfied by *rephrasing* rather than by the
`process` marker — evidence the gate checks the shape of coupling
(strings) rather than its substance (subprocess calls). Two strikes:
per `two_strike_split`, the discriminator belongs in code — e.g., flag
modules that import `subprocess`/`os.system` alongside boundary
strings, not the strings alone.

**Seed:** Should re-entry guards be generated from a role manifest
(allowed tools, banned launch surfaces) instead of hand-written prose?
The judge, reviewer, and author adapters now carry three hand-tuned
variants of the same guard; a fourth variant is the
`regex_fourth_exclusion` moment for guard prose.
