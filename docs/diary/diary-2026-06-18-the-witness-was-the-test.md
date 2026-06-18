# The Witness Was the Test the Unit Tests Couldn't Be

**FR-519 — DM v2 intra-chapter prose-vs-state enforcement (Phase 1)**

## What happened

I judged FR-519 with one must-fix blocker (B1): the proposed solution read the
chapter's own `world_state` to find within-chapter deaths, but I'd verified that
`close_chapter` computes that `world_state` *after* the final cut runs — it's empty
at the moment the fix wanted to read it. The frozen redraft threaded the close-graph
output `closed` into `invoke_final_cut` instead. Enforcement followed the redraft:
new `dead_character_names`, a possession block, three Jinja-guarded prompt sections,
warn-only diagnostics. All 196 DM unit tests went green.

Then the witness — re-closing chapter 6 of 10021-BC — failed on the first run with
`Missing required variable(s): dead_before_open, dead_within_chapter,
possession_facts`. The unit tests had mocked `invoke_final_cut`, so they never
exercised the real graph. The graph YAML's `state:` schema and node `variables:`
still declared the *old* `dead_characters` key; LangGraph silently dropped the three
new keys before they reached the prompt. Green unit tests, broken integration.

## The trap

**`mock_escape_hatch` met `architecture_as_diagram`.** The unit tests mocked the
exact seam (the graph invocation) where the contract lived. A graph state key is a
*contract* between the Python context-builder and the prompt — but it's declared in
YAML, invisible to the Python type checker and bypassed by the mock. I treated the
context dict (`final_cut_context`'s return) as the boundary, when the real boundary
was one layer deeper: the graph's declared state schema. The keys existed in Python
and were dropped at the YAML boundary I hadn't enumerated.

## The insight

The witness wasn't a formality appended after "done" — it was the only test that
crossed the Python→YAML→prompt boundary end-to-end. Doctrine says *demos prove the
abstraction is worth having; tests prove constraints*. Here the demo proved the
constraint the tests structurally could not: that the new variables survive the
graph. **When a unit test mocks the component that owns the contract, the contract
is untested by definition.**

And the witness paid a second dividend: it turned an ambiguous acceptance criterion
("findings clear OR FR-520 gate triggered") into a decision. Possession cleared (the
staff is handled passively now). Within-chapter death did *not* — Hagan still acts
after he's struck down, because the *played arc itself* has him acting across turns
11–16, and the final-cut prompt can't reconcile that without breaking beat-fidelity.
That's not a Phase 1 failure; it's the precise, evidenced entry condition FR-520 was
gated on. Phase 1's honest job was to prove prompt injection insufficient for death —
and it did, with a named excerpt instead of a hunch.

## Heuristic

When enforcing a change that flows Python → graph YAML → prompt, **a passing unit
suite that mocks the graph invocation is not evidence the wiring works.** Run one
real end-to-end witness before declaring done; declare the graph state schema a
boundary to enumerate (add/rename a context key → grep the graph `state:` and
`variables:` in the same edit). The mock hides the one seam most likely to drift.

**Seed:** Could a lint rule cross-check that every key returned by a `*_context`
function appears in its graph's `state:` schema — turning this silent YAML-boundary
drop into a mechanical failure instead of a witness-only one? The context builder and
the graph schema are two halves of one contract written in two languages; nothing
currently asserts they agree.
