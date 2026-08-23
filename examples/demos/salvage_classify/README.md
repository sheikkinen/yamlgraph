# Salvage Classify Demo

Classifies every tracked file of a frozen source repository (the stale
`scripture-dev` distributor, FR-868) against this repo's current
equivalents, emitting a human-review disposition draft: `duplicate`
(names the equivalent here), `lift` (destination under `ramp/salvage/`),
or `obsolete`. No `unknown` verdicts; count-in == count-out over the
manifest.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/salvage_classify/graph.yaml

# Run against a frozen checkout
yamlgraph graph run examples/demos/salvage_classify/graph.yaml \
  --var source_repo=/path/to/scripture-dev \
  --var source_sha=9d4677a9d501b686d1408d69145debc5c116dd99
```

## What It Does

1. Collects the tracked-file manifest at the frozen ref (`git ls-files`)
2. Classifies each file against this repo's equivalents (map node)
3. Validates the disposition: count reconciliation, duplicate
   equivalents exist, lift destinations confined to `ramp/salvage/`
4. Writes `tmp/ramp/salvage-disposition.{md,json}` for human review

## Output

Drafts only. Lifting files and archiving the source repo are human acts
gated by FR-868 (raw-output read, secret scan, written approval).
