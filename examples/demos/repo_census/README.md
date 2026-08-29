# Repo Census demo

GitHub organization repository census for FR-899. The graph discovers a
bounded repository list, extracts one evidence bundle per repository, asks
Azure for one purpose judgement per repository, writes a deterministic ledger,
and renders one portfolio brief through the existing corpus-census citation
boundary.

Smoke invocation against the public demo org:

```bash
yamlgraph graph run examples/demos/repo_census/graph.yaml \
  --tool discover=examples/demos/corpus_census/adapters/gh-org-discover.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/gh-repo-extract.tool.yaml \
  --var source="sheikkinen:2" \
  --var rubric="State this repository's purpose in one sentence: what it does and for whom." \
  --var output_path=tmp/repo-census-smoke.md \
  --var brief_path=tmp/repo-census-smoke-brief.md \
  --var brief_rubric="Summarize this organization's repository portfolio." \
  --full
```

`AZURE_MODEL` selects the Azure deployment; `AZURE_AI_ENDPOINT`,
`AZURE_AI_API_KEY`, and `AZURE_MODEL` must be set before the graph performs
GitHub discovery. The preflight node blocks unconfigured runs before any
repository data is fetched. Customer organizations are runtime `--var` input
only, and their outputs are never committed.
