# Session Shapes Demo

FR-884 dogfoods YAMLGraph for bulk session task-shape classification. It reads
session skeleton JSONL, maps one pinned Haiku judgement over each session, then
aggregates counts and token-weighted shape shares deterministically.

Run:

```bash
yamlgraph graph run examples/demos/session-shapes/graph.yaml \
  --var input_file=examples/demos/session-shapes/fixtures/synthetic-sessions.jsonl \
  --full
```

The classifier is pinned to `provider: anthropic` and
`model: claude-haiku-4-5` because FR-884 needs a cheap, consistent mini model
for many independent session judgements.

Privacy note: the only written output is `tmp/fr884-classified.json`, and the
aggregate step writes shape ids, fractions, counts, and session ids only. It
does not echo transcript skeleton text.
