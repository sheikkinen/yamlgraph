# The generator without a verifier

**Date:** 2026-09-09
**Series:** metamodelling, part 1
**Trigger:** operator: "metamodelling — llm has all the knowledge and can
answer to any question but lacks the feedback loop to crosscheck every
piece of information generated. compare to repo harness … reflect — how
to generalize, how to help llm to get similar support on any given task."
**Context:** no FR; a reflection on what this repository's harness *is*,
written by the thing the harness is for.

## The asymmetry

An autoregressive generator has no rollback and no independent checker.
The weights that produced token *n* judge token *n+1*, with the error
already in context as an anchor. Knowledge is not the constraint;
verification is. The harness in this repository is therefore not
"process". It is an externalised second system, and every component is
one `(boundary, oracle, action)` triple bolted onto a generator that has
none of its own.

| Component | Generator error it catches | Oracle | Boundary | Action |
|---|---|---|---|---|
| TDD, RED before GREEN | `continuation_bias`, `plausible_wrong_answer` | mechanical, pre-committed | before generation | fail |
| CC / 400-line cap, `radon`, `.importlinter` | `growth_as_default`, `architecture_as_diagram` | mechanical entropy proxy; needs no notion of correctness | commit | block |
| RTM: `@pytest.mark.req`, `req_coverage.py --strict` | `intent_drift` | reference artifact | CI | block |
| PreToolUse / PostToolUse hooks | `vendor_default_as_help`, `skip_env_as_bypass` | mechanical | the tool call, before effects exist | deny |
| Skills | variance on repeated tasks | procedural memory | before generation | shape the prompt |
| Judge, reviewer, outsider with input closure | `quick_confidence`, `private_language`, `model_as_trusted_peer` | independent LLM | PR | advisory, then human |
| Diary → Scripture | the weights do not update | the harness learns instead | cross-session | amend the harness |

Two properties recur in every row that works. The check is **fixed
before the output exists**, so it cannot be rationalised after the fact.
The oracle is **cheaper than the generation**, so it runs every time
rather than when someone remembers.

The judge row carries the transferable trick. Separation of weights is
not available; the judge runs on the same model family as the author.
What the doctrine substitutes is **separation of context**: the judge
sees the FR and the repo, never the author's chat (`judge-fr/doctrine.md`
input closure); the outsider sees the PR body and nothing else (FR-995).
The anchor that biases the author is absent from the checker's window.
That is the closest an LLM harness gets to an independent verifier
without a compiler.

## What code got for free

Compilers, type checkers, tests, coverage: decades of mechanical oracles.
Code is the domain where LLM delegation works best not because models are
better at code but because code is the domain where *you* can afford to
check. This repository's own invention begins where the mechanical
oracles run out, at FRs, research records, prose: rubric and input closure
first, then render. TDD for artifacts a compiler cannot see.

## Generalisation: verifier first

For any task X handed to a generator, before generating:

1. **Write the falsifiable claim.** What will be true of the output that
   is false now? If it cannot be stated, a draft is being commissioned,
   not a deliverable. Prose RED: "a reader given only this can do Y."
2. **Name the oracle and its rung.** Mechanical → reference artifact →
   independent LLM with input closure → human → reality (run it, trace
   it). Descend one rung at a time and say which rung is in use.
3. **Find the cheapest boundary.** Where does a wrong move become
   expensive? Block there: the tool call, the commit. A hook at the
   action beats a reviewer after the effect.
4. **Cap entropy without a correctness oracle.** Length, fan-out,
   nesting, hedge density: CC for whatever the artifact is. It catches
   rot before wrongness can be caught.
5. **Thread traceability both ways.** Every output element points at a
   stated intent; every intent has an output. Orphans in either
   direction are the drift.
6. **Encode the repeat.** Third recurrence → skill. Re-derivation is
   where variance re-enters.
7. **Route failures to the harness, not the model.** The model will not
   remember. Each incident becomes a new triple, or an explicit refusal
   to add one.
8. **Harness edits go through the harness.** Under pressure the
   generator widens the gate that caught it (`guard_widening_when_caught`,
   `instruction_boundary_uncrossed`). Changes to enforcement are
   adversarial input by construction.

Corollary that alters decisions: **the delegable surface of a task equals
its verifiable surface.** Where no verifier can be built, the output is a
hypothesis with good typography.

## Where the harness is honest about itself

- Non-code artifacts have shape gates plus one substance oracle, the
  judge. `gate_checks_shape_not_substance` is named, not solved;
  `proof_by_placement`-class gaming remains possible.
- The harness has its own `growth_as_default`. Scripture grows, hooks
  slow, and there is no entropy cap on the harness. Rule 8 cuts both
  ways: pruning a triple needs the same FR and judge as adding one.
- Skills encode the first solution that worked. Nothing says when a
  skill has decayed.

This is the V-model for a stochastic generator, requirement-to-test
tracing from IEC 62304 territory applied to an author that produces the
whole left side of the V in one pass and none of the right. The harness
is the right side.

## Traps

**`knowledge_as_capability`.** Treating "the model knows X" as "the model
can be trusted with X". Knowledge without an external check is a
generator, and a generator's confidence is a property of its sampling,
not of the world.

**`verifier_after_the_fact`.** A check designed after the output exists
inherits the output's framing. The RED discipline is not a testing habit;
it is the only position from which the check is independent.

## Heuristic

Before delegating any task, build the verifier's table first: claim,
oracle rung, boundary, action. If the table has an empty row, that row is
where the generator will be wrong and nobody will notice.

**Seed:** the harness has no harness. Is there an entropy metric for the
Scripture and hook set themselves, and which boundary would fire it? Part
2 of this series should attempt the census: enumerate every triple in
`.github/`, `scripts/`, and `.pre-commit-config.yaml`, and mark which have
fired in the last ninety days and which have only ever been satisfied.
