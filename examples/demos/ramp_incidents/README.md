# Ramp Incident Reconciliation Demo

Reconciles a target repository's failure narratives (diary entries, FR
post-mortems) into a deduplicated incident register draft for human review
(FR-866).

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/ramp_incidents/graph.yaml

# Run against a named target corpus
yamlgraph graph run examples/demos/ramp_incidents/graph.yaml \
  --var target_name=deviant-daily
```

## What It Does

1. Collects the target's failure-narrative corpus
2. Classifies each document into incident candidates (map node)
3. Merges and deduplicates candidates; a count validator names any document
   lost to a truncated branch (fails loudly rather than silently dropping)
4. Writes `tmp/ramp/incidents-draft.{md,json}` for human review

## Output

Incident register draft: one entry per distinct incident with source
documents, boundary classification, and proposed trap/cure linkage.
