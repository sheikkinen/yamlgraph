# Feature Request: Repair the safety-guards demo so it compiles and routes as documented

**Priority:** MEDIUM
**Type:** Bug (demo)
**Status:** Proposed
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
through the graph-authoring route and proves the revise-loop count.
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
`revise` only, not to `[revise, expand]`. Do it through `scripts/author.sh`,
and record lint, compile and a smoke run that shows how many times each node
ran.

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

1. Write a task brief and run `scripts/author.sh <brief>`. Every change to
   `graph.yaml` or `prompts/*.yaml` goes through that route
   ([.github/skills/graph-authoring/doctrine.md](../.github/skills/graph-authoring/doctrine.md));
   this FR does not edit the demo directly.
2. The brief asks for one change: `to: [revise, expand]` becomes
   `to: revise` on the low-score edge. Both conditional edges from `review`
   then compile as expression edges into one router
   (`yamlgraph/compile/edge_compiler.py#L256-L261`); a conditional edge to a
   map node resolves to the map's fan-out inside that router (FR-467 comment,
   `#L257-L258`).
3. The brief asks the authoring run to report the W803 gap as found and to
   either close it or state it in the README. The README line "should pass
   clean" is corrected to match the recorded lint output. `README.md` is
   not a governed graph artifact.
4. The authoring report records: lint output, a successful compile, and one
   smoke run with the node visit sequence.

## Acceptance Criteria

- [ ] AC-01: the repaired graph compiles (`load_graph_config` +
  `compile_graph` + `.compile()`), recorded in the authoring report. After
  [FR-1086](FR-1086-lint-compile-check.md) lands, `graph lint --build` on it
  reports no errors.
- [ ] AC-02: the diff to `graph.yaml` is limited to the low-score edge,
  plus any W803 change the report justifies.
- [ ] AC-03 (revise-loop count, FR-1069 judgement AC-04): the smoke run's
  node visit sequence is recorded. `revise` runs at most 3 times, `expand`
  runs exactly once, and `expand` starts only after the last `review`.
- [ ] AC-04: the README lint line matches the recorded lint output.
- [ ] AC-05: the change was made through `scripts/author.sh`, witnessed by
  `tmp/draft-authoring-report.md` from that run, not by exit code.
- [ ] AC-06: changelog fragment, FR implementation record, diary entry.

## Alternatives Considered

Solution classes (chosen: 1):

1. **Two expression edges: low score → `revise`, high score → `expand`.**
   Chosen. One-word change; matches the comment and the second edge already
   in the file.
2. **`type: conditional` with a list of routes.** Preserved dissent: it is
   the first fix the compiler's error message suggests. It loses because
   that shape feeds `router_edges` (`edge_compiler.py#L61-L64`,
   `#L252-L253`), which serves router nodes. `review` is an `llm` node, so
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
Changing what the runtime does when `loop_limits` is reached. Whether
`review: str` in the `state:` block (`graph.yaml#L32`) fits the `Review`
schema output (`prompts/review.yaml`); the smoke run will show it, and a
failure there is reported in the authoring report, not fixed silently.

## Related

- Split from: [FR-1069](FR-1069-lint-builds-graph.md)
- Sibling: [FR-1086](FR-1086-lint-compile-check.md)
- Demo origin: [027-execution-safety-guards.md](027-execution-safety-guards.md)
- Error source: [FR-718](FR-718-edge-compiler-decomposition.md)
- Authoring route: [.github/skills/graph-authoring/doctrine.md](../.github/skills/graph-authoring/doctrine.md)
