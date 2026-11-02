# Smart If Demo

A decision node asks inline, typed questions about graph state and returns
normalized probabilities instead of generating text. This is the decision
analog of [`demos/hello`](../hello/): the smallest runnable example of one core
node, with deterministic branching and no prompt file.

## Quickstart

```bash
yamlgraph graph lint examples/demos/smart-if/graph.yaml
yamlgraph graph run examples/demos/smart-if/graph.yaml --var message="Database outage in production" --full
yamlgraph graph run examples/demos/smart-if/graph.yaml --var message="Please update the newsletter footer" --full
```

The first run takes the `escalate` branch and ends with
`outcome: escalated`; the second takes the `archive` branch and ends with
`outcome: archived`.

The `mock` provider uses planted, deterministic substring rules, so this demo
is keyless. For a real provider, set `provider: system_one_adapter`, add
`model: "openai:gpt-4o-mini"`, and install the `decision` extra.

## Validation

Both run commands were executed with the worktree-local CLI. They completed
without API keys and visited the two documented branches. Lint initially
reported E005 because the linter's node-type registry omitted the new
`decision` type; after the FR-1155 linter fix, lint passes with 0 errors and
one advisory W803 (the theoretical unset-state fall-through, which the
unconditional gate node makes unreachable in practice).
