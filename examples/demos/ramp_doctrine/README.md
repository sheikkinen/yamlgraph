# Ramp Doctrine Tailoring Demo

Judges each YAMLGraph Scripture entry (traps, cures, questions) for
transferability to a target repository and writes a human-review draft
disposition (FR-866). Source-repo incident citations are scrubbed at the
write boundary.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/ramp_doctrine/graph.yaml

# Run against a target repo
yamlgraph graph run examples/demos/ramp_doctrine/graph.yaml \
  --var target_path=tests/fixtures/ramp_target --full
```

## What It Does

1. Collects the Scripture inventory (traps, cures, questions)
2. Judges each entry's transferability against the target repo's inventory (map node)
3. Merges dispositions and writes `tmp/ramp/doctrine-draft.{md,json}` for human review

## Output

Draft disposition files under `tmp/ramp/` — kept entries with rationale,
dropped entries with reasons. All FR-XXX/NC-XXX citations replaced with
"a source-repo incident".
