# Pattern Model Census demo

Read-only commit-metadata census for FR-896. The graph mirrors
`examples/demos/corpus_census/`: callers bind `discover` and `extract` slots at
run time, two mercury-pinned map passes classify one lens each, and an LLM-free
reducer writes a private JSONL working ledger plus a public-safe aggregate
markdown summary.

Fixture smoke:

```bash
yamlgraph graph run examples/demos/pattern_model_census/graph.yaml \
  --tool discover=examples/demos/pattern_model_census/fixtures/discover.tool.yaml \
  --tool extract=examples/demos/pattern_model_census/fixtures/extract.tool.yaml \
  --var source=examples/demos/pattern_model_census/fixtures/commits.json \
  --var repo_alias=fixture-demo \
  --var output_path=tmp/pattern-model-census-fixture-ledger.md
```

Production callers bind `tools/git_discover.tool.yaml` and
`tools/git_extract.tool.yaml` when running against an explicitly authorized git
repository. The extractor returns commit metadata only: `repo`, `sha`, `date`,
`subject`, and `shortstat`.
