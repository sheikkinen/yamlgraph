# First-Class Verification Demo (FR-677)

Demonstrates the three verification constructs added in FR-677, all offline
(no LLM, no provider key):

1. **Node guards on a side-effect node** — `guards.pre`/`guards.post` on a
   `type: python` tool node (previously only llm/router/copilot honored guards).
2. **Graph-level `verify:` block** — a graph-wide postcondition evaluated once
   against the final state through an inserted terminal `__verify__` node.
3. **`--gate`** — lint the graph before running and refuse to execute on any
   error-level finding.

## What it shows

- **Pre guard (`halt`)**: aborts the node when `readings` is empty.
- **Post guard (`warn`)**: logs a warning if the computed `score` is negative.
- **Graph `verify:` (`halt`)**: fails the whole run when the final `score` is
  below the acceptance threshold (`>= 100`).
- **`--gate`**: runs the linter first; a clean graph passes straight through.

## Run

```bash
# Passing run: readings sum to 105, clears the verify threshold
printf 'readings: [40, 35, 30]\n' > /tmp/pass.yaml
yamlgraph graph run examples/demos/verification/graph.yaml --var-file /tmp/pass.yaml --full

# Verify halt: readings sum to 60, below the threshold -> graph halts
printf 'readings: [20, 20, 20]\n' > /tmp/fail.yaml
yamlgraph graph run examples/demos/verification/graph.yaml --var-file /tmp/fail.yaml --full

# Pre-guard halt: empty readings -> node pre-guard halts before execution
printf 'readings: []\n' > /tmp/empty.yaml
yamlgraph graph run examples/demos/verification/graph.yaml --var-file /tmp/empty.yaml --full

# Lint gate: lint first, refuse to run on any error-level finding
yamlgraph graph run examples/demos/verification/graph.yaml --var-file /tmp/pass.yaml --gate --full
```

See [demo-output.log](demo-output.log) for the gate-passing proof, and
[run-transcript.log](run-transcript.log) for the full capture of all four
scenarios (the halt scenarios intentionally emit error markers).
