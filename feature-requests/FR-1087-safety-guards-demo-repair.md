# Feature Request: Repair the safety-guards demo so it compiles and routes as documented

**Priority:** MEDIUM
**Type:** Bug (demo)
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1087-safety-guards-demo-repair.judgement.md)); R-1–R-4 folded 2026-09-26. Authority active (2026-09-26): human review recorded — operator instruction 'proceed with all fr changes' (2026-09-26). **Completed 2026-09-26** — see [Implementation](#implementation-2026-09-26).
**Authoring brief:** [authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md](authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md)
**Effort:** 0.25 days
**Requested:** 2026-09-25
**First consumer / first event:** the README quick start,
`yamlgraph graph run examples/demos/safety-guards/graph.yaml --var
topic="quantum computing" --var topics='["physics", "math", "biology"]'`
(`examples/demos/safety-guards/README.md#L12-L15`). It fails at compile time,
before any LLM call, because of the edge at
`examples/demos/safety-guards/graph.yaml#L81-L83`.
**Research:** FR-890 research route not run. Operator decision 2026-09-25
for the FR-1069 refile: "refile. skip research — document as skipped". The
substitute is the in-body Alternatives Considered section below (four
solution classes, one chosen, one preserved dissent, `is_this_a_graph`
answered). Four, not six: the edge grammar has a fixed set of shapes
(`EdgeShape`, `yamlgraph/compile/edge_compiler.py#L22-L32`), and the
classes below are every shape that can express "review decides between
revise and expand".
**Prior art:**
[FR-1069](FR-1069-lint-builds-graph.md) (SPLIT). This is its demo-repair
half; the lint check is [FR-1086](FR-1086-lint-compile-check.md).
Judgement R-1: the demo is fixed without any lint change. R-3: solution
classes, dissent and `is_this_a_graph` below. AC-04 and C-2: the repair goes
through the graph-authoring route, and a deterministic test proves the
revise-loop path (AC-04, AC-05 below).
[027-execution-safety-guards.md](027-execution-safety-guards.md). The FR
that created this demo; `git log` shows the demo directory last changed in
`b6312cdb` (2026-02-10, FR-027).
[FR-718](FR-718-edge-compiler-decomposition.md) (Completed 2026-07-12). Its
status line says a condition on a fan-out list "now raises (was silently
dropped)". So before FR-718 this demo compiled with the condition ignored,
and a low-score review started both `revise` and `expand`. After FR-718 it
does not compile.
[FR-234](FR-234-parallel-fan-out-edges.md). Defines fan-out list edges.

## Summary

Change one edge in the safety-guards demo: a low review score goes to
`revise` only, not to `[revise, expand]`. Do it through `scripts/author.sh`
with the committed brief. Correct the README's lint promise. Add a
deterministic test that drives a low then a high review score and checks the
exact node order.

## Value Statement

The FR-027 example of loop guards, map caps and recursion limits runs again,
and shows the intended draft → review → revise loop with a single final
`expand`.

## Problem

- The edge `from: review, to: [revise, expand], condition: "review.score <
  0.8"` (`examples/demos/safety-guards/graph.yaml#L81-L83`) is a fan-out
  list with a condition and no `type: conditional`. `classify_edge` sends it
  to `_classify_fanout` (`yamlgraph/compile/edge_compiler.py#L91-L92`),
  which raises `ValueError` (`#L35-L43`).
- The intent is a loop, per the comment "Cycle: review → revise → review"
  (`graph.yaml#L80`) and the second edge `review → expand` when
  `review.score >= 0.8` (`graph.yaml#L85-L87`). Listing `expand` on the
  low-score edge would start the map on every revise pass.
- The README says "Lint — should pass clean"
  (`examples/demos/safety-guards/README.md#L9`). Plain lint today reports 0
  errors and 1 warning: W803, "Condition gap at 'review': state
  (review.score = <missing>) falls through when unset — runtime silently
  routes to END" (run 2026-09-25; W803 comes from the optional z3 check,
  `yamlgraph/linter/patterns/conditions_smt.py`).

## Ideal Result

The demo compiles. A run visits draft, then review and revise alternately
within the `loop_limits` of 3 (`graph.yaml` `loop_limits`), then `expand`
once. The README's lint and run commands describe what actually happens.

## Proposed Solution

1. Run `scripts/author.sh feature-requests/authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md`.
   The brief is committed and cited above, as the authoring doctrine
   requires for FR-bound briefs
   ([.github/skills/graph-authoring/doctrine.md](../.github/skills/graph-authoring/doctrine.md#L26-L30)).
   Every change to `graph.yaml` goes through that route; this FR does not
   edit the graph directly.
2. The brief asks for one change: `to: [revise, expand]` becomes
   `to: revise` on the low-score edge. Both conditional edges from `review`
   then compile as expression edges into one router
   (`_compile_expression`, `yamlgraph/compile/edge_compiler.py#L222-L226`;
   router built at `#L367-L377`). A map target is its own dispatch node, so
   `expand` is routed like any other node (FR-1073 comment, `#L223`).
3. W803 gets documentation only, no graph change. The README line "should
   pass clean" (`examples/demos/safety-guards/README.md#L9`) is replaced
   with a statement that lint reports W803 when the optional z3 condition
   check is available. `README.md` is not a governed graph artifact, so this
   edit is made outside the authoring run.
4. New test `tests/unit/test_safety_guards_demo.py` compiles the graph and
   runs it with deterministic structured review results: a score below
   `0.8`, then one at or above `0.8`. It asserts the node order
   `draft, review, revise, review, expand`. A single live LLM run can take
   the high-score edge at once and never exercise the repaired edge, so it
   cannot be the proof.
5. The authoring report (`tmp/draft-authoring-report.md`) records: the
   exact lint command and output and whether z3 was available; the exact
   compile command and outcome; and one attempted README run with its
   command, node sequence and outcome, or the exact blocker.

## Acceptance Criteria

- [x] AC-01: `feature-requests/authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md`
  is committed, cited by FR-1087, names the frozen artifact boundary, and is
  the task passed to `scripts/author.sh`.
- [x] AC-02: the complete `graph.yaml` diff changes only `to: [revise, expand]`
  to `to: revise` on the `review.score < 0.8` edge.
- [x] AC-03: the authoring report records the exact command and successful
  outcome for `load_graph_config` + `compile_graph` + `.compile()` on
  `examples/demos/safety-guards/graph.yaml`.
- [x] AC-04: `tests/unit/test_safety_guards_demo.py` deterministically drives
  review scores below and then at or above `0.8` and asserts the exact node
  sequence `draft, review, revise, review, expand`.
- [x] AC-05: the same deterministic witness asserts `revise` runs once,
  `expand` runs exactly once, and no `expand` visit precedes the last
  `review`.
- [x] AC-06: the authoring report records the exact lint command and output,
  identifies whether the optional z3 check was available, and the README no
  longer promises a clean lint; it documents W803 when that check is
  available.
- [x] AC-07: the documented CLI run is attempted with the README variables
  and its exact command, node sequence, and outcome are recorded; if
  credentials or a dependency block it, the report records the exact blocker
  and does not claim success.
- [x] AC-08: `tmp/draft-authoring-report.md` contains the required
  `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation`
  headings and identifies the FR-1087 brief and authored paths.
- [ ] AC-09: one `changelog/unreleased/` fragment names FR-1087; FR-1087
  records implementation decisions and completed status; one `docs/diary/`
  entry names FR-1087 and contains `Seed:`.

## Scope (frozen by judgement)

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md` |
| D-2 | `examples/demos/safety-guards/graph.yaml` — low-score edge target only |
| D-3 | `examples/demos/safety-guards/README.md` — lint expectation only |
| D-4 | `tests/unit/test_safety_guards_demo.py` — deterministic compile and route witness |
| D-5 | `tmp/draft-authoring-report.md` — authoring-route validation record |
| D-6 | FR-1087 implementation record, one FR-1087 changelog fragment, and one FR-1087 diary entry |

Not authorized: changes to linter behavior or FR-1086; compiler, runtime,
loop-limit, state-schema, or prompt changes; a W803 fallback edge or other
W803 graph repair; edits to any other graph or demo; dependency additions;
or changes to the documented safety-feature set.

Enforcement conditions C-1–C-5 are in the
[judgement](FR-1087-safety-guards-demo-repair.judgement.md#conditions-for-enforcement)
and are all GATEs: revisions folded first (C-1, met 2026-09-26); graph work
only inside the authoring run launched with the committed brief (C-2); the
graph diff is exactly the one edge target and W803 is documentation only
(C-3); no live LLM run in place of the deterministic witness (C-4); no lint,
compiler, runtime, loop-limit, schema, prompt, dependency or other-demo
changes (C-5).

## Human decisions

- **2026-09-26, operator:** reviewed the advisory judgement and instructed
  "proceed with all fr changes". R-1–R-4 are folded as written and
  authority is active under the frozen scope above.

## Implementation (2026-09-26)

- **Route (AC-01, C-2).** `scripts/author.sh feature-requests/authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md`
  from the `feat/fr1087-1088-demo-repairs` worktree, exit 0, report verified
  (all five headings; authored path `examples/demos/safety-guards/graph.yaml`).
  First attempt stopped at the brief pre-flight: it parsed the
  backslash-continued README command as the executable `--var`. The brief's
  command was put on one line (same command); no other brief change.
- **Graph diff (AC-02, C-3).** Exactly `to: [revise, expand]` → `to: revise`
  on the `review.score < 0.8` edge. Author precedent cited:
  `examples/demos/reflexion/graph.yaml` (split score conditions).
- **Compile (AC-03).** `load_graph_config` + `compile_graph` + `.compile()`
  printed `compiled_type=CompiledStateGraph`, exit 0.
- **Lint (AC-06).** `yamlgraph graph lint examples/demos/safety-guards/graph.yaml`:
  `Found 0 error(s) and 1 warning(s)`, the W803 condition gap at `review`.
  z3 was available (W803 is emitted only by the z3 check). README line 9
  now says 0 errors plus W803 when z3 is available.
- **Deterministic witness (AC-04, AC-05, C-4).**
  `tests/unit/test_safety_guards_demo.py` patches
  `llm_nodes.execute_prompt`, scripts review scores 0.3 then 0.9, and reads
  top-level node updates from `graph.stream(stream_mode="updates")`, counting
  the map's per-item updates as one `expand` visit. RED at HEAD: 2 failed
  with the `edge_compiler.py:38` fan-out `ValueError`. GREEN: 2 passed.
- **Live run (AC-07).** README command attempted with `openai/gpt-4o`.
  Sequence `draft, review` → route `review.score >= 0.8` → `expand`, then
  exit 1: `Map 'over' must resolve to list, got str`. The CLI passes
  `--var topics='[...]'` as a string, so the map cannot fan out. Not fixed:
  the Out of scope section reserves runtime findings for the report, and
  C-5 forbids state-schema and runtime changes. The high-score edge was
  taken first, so the live run did not exercise the repaired edge; the
  deterministic witness does.
- **Demo proof.** The `demo-proof-check` hook requires a successful
  `demo-output.log` for a changed demo. The committed
  `examples/demos/safety-guards/demo-output.log` is from this `graph.yaml`,
  run with the README variables in a YAML var file so `topics` arrives as a
  list: `yamlgraph graph run examples/demos/safety-guards/graph.yaml --var-file <topic + topics list> --full`,
  exit 0. Sequence `draft, review` → `review.score >= 0.8` → `expand`
  (fan-out 3). The README's `--var topics='[...]'` form still fails as
  above; fixing the README command is outside D-3.
- **Report (AC-08).** `tmp/draft-authoring-report.md` stays local, as
  doctrine requires; the commands and outcomes above are copied from it.

## Alternatives Considered

Solution classes (chosen: 1):

1. **Two expression edges: low score → `revise`, high score → `expand`.**
   Chosen. One-word change; matches the comment and the second edge already
   in the file.
2. **`type: conditional` with a list of routes.** Preserved dissent: it is
   the first fix the compiler's error message suggests. It loses because
   that shape feeds `router_edges` (`edge_compiler.py#L61-L64`,
   `#L218-L219`), which serves router nodes. `review` is an `llm` node, so
   this needs a new router node and grows the demo.
3. **Unconditional fan-out `review → [revise, expand]`.** Rejected: it is
   what the graph did before FR-718, and it runs the map on every revise
   pass.
4. **Delete the demo.** Rejected: it is FR-027's worked example and the
   README documents all four safety features against it.

`is_this_a_graph`: the fix is to a graph, but deciding the fix is not a
model task. The edge shape is fixed by the compiler grammar.

## Out of scope

Any change to lint (FR-1086). Other broken graphs found by FR-1086's census.
Changing what the runtime does when `loop_limits` is reached. Closing the
W803 condition gap in the graph. Whether `review: str` in the `state:` block
(`graph.yaml#L32`) fits the `Review` schema output (`prompts/review.yaml`);
the CLI run will show it, and a failure there is reported in the authoring
report, not fixed under this FR.

## Related

- Split from: [FR-1069](FR-1069-lint-builds-graph.md)
- Sibling: [FR-1086](FR-1086-lint-compile-check.md)
- Demo origin: [027-execution-safety-guards.md](027-execution-safety-guards.md)
- Error source: [FR-718](FR-718-edge-compiler-decomposition.md)
- Authoring route: [.github/skills/graph-authoring/doctrine.md](../.github/skills/graph-authoring/doctrine.md)
- Authoring brief: [authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md](authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md)
