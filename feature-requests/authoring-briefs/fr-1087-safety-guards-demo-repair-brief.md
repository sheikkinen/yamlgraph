# FR-1087 brief — safety-guards demo: low-score edge goes to `revise` only

**Prior art:** `fr-1050-demo-loop-limit-migration-brief.md` is the closest
shape (a one-block repair of an in-repo demo that stopped loading after a
compiler change). No earlier brief touches `examples/demos/safety-guards/`;
the demo was created by `feature-requests/027-execution-safety-guards.md`.

## Task

`examples/demos/safety-guards/graph.yaml` no longer compiles. Its edge from
`review` puts a condition on a fan-out list, which the compiler rejects
(`yamlgraph/compile/edge_compiler.py#L35-L43`). The intent, per the comment
above the edge, is a loop: a low review score goes back to `revise`; a high
score goes on to `expand`. Make the low-score edge point at `revise` only.

## Edit (exact; nothing else)

In `examples/demos/safety-guards/graph.yaml`, on the edge

```yaml
  - from: review
    to: [revise, expand]
    condition: "review.score < 0.8"
```

change `to: [revise, expand]` to `to: revise`.

Leave every other line of `graph.yaml` unchanged: nodes, other edges,
`state`, `config`, `loop_limits`, and comments. Do not add a fallback edge or
any other change for lint warning W803. Do not edit `prompts/*.yaml`,
`README.md`, tests, or any other graph. The README correction and the
deterministic route test are FR-1087 deliverables D-3 and D-4, done outside
this authoring run.

## Validation

Record each item under `Validation` in `tmp/draft-authoring-report.md`, or
under `Blocked validation` with the exact blocker:

1. Lint — record the exact command and full output:

   ```bash
   yamlgraph graph lint examples/demos/safety-guards/graph.yaml
   ```

   State whether the optional z3 condition check was available (when z3 is
   missing the linter reports one info issue instead of running the check).
   W803 on `review` is expected when z3 is available; report it, do not fix it.

2. Compile — record the exact command and outcome of
   `load_graph_config` + `compile_graph` + `.compile()` on the graph.

3. Run — attempt the README command and record the exact command, node visit
   sequence, and outcome:

   ```bash
   yamlgraph graph run examples/demos/safety-guards/graph.yaml \
     --var topic="quantum computing" \
     --var topics='["physics", "math", "biology"]'
   ```

   If credentials or a dependency block the run, record the blocker and do
   not claim success. A live run may take the high-score edge first and
   never exercise the repaired edge; that is expected and is not a failure.

## Governing FR

`feature-requests/FR-1087-safety-guards-demo-repair.md` (D-1, D-2, D-5;
AC-01–AC-03, AC-06–AC-08) and its judgement
`feature-requests/FR-1087-safety-guards-demo-repair.judgement.md`
(gates C-2, C-3, C-5).
