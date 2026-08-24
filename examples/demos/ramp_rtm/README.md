# Ramp RTM Derivation Demo

Derives candidate requirements (REQ-XXX) for a target repository from its
own inventory, producing a requirement-traceability-matrix draft for human
review (FR-866).

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/ramp_rtm/graph.yaml

# Run against a target repo
yamlgraph graph run examples/demos/ramp_rtm/graph.yaml \
  --var target=tests/fixtures/ramp_target --full
```

## What It Does

1. Collects the target repo inventory (modules, tests, configs)
2. Derives candidate requirements per module (map node)
3. Identifies coverage gaps (modules with no testable claim)
4. Writes `tmp/ramp/rtm-draft.{md,json}` for human review

## Output

RTM draft with candidate REQ IDs, per-module traceability, and a gap list.
IDs are drafts — the target repo assigns its own namespace on adoption.
