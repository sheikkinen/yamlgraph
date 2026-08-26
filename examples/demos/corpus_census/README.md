# Corpus Census demo

Shared census pipeline for FR-892. The graph does not hardcode corpus
discovery or extraction: callers bind `discover` and `extract` slots at run time
with FR-768 manifests.

```bash
yamlgraph graph run examples/demos/corpus_census/graph.yaml \
  --tool discover=fixtures/discover.tool.yaml \
  --tool extract=fixtures/extract.tool.yaml \
  --var source=examples/demos/corpus_census/fixtures/corpus \
  --var rubric="classify each document's main topic in one word" \
  --var output_path=tmp/corpus-census-ledger.md
```
