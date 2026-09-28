# LangGraph issues census

Classifies `langchain-ai/langgraph` issues and pull requests into the frozen
FR-1130 taxonomy, writes a normalized ledger, then emits crosstab and manifest
artifacts.

## Full census

```bash
set -a; . ./.env; set +a
yamlgraph graph run examples/demos/langgraph_issues_census/graph.yaml \
  --tool discover=examples/demos/corpus_census/adapters/gh-issues-discover.tool.yaml \
  --tool versions=examples/demos/corpus_census/adapters/gh-issues-versions.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/gh-issues-extract.tool.yaml \
  --var source=langchain-ai/langgraph \
  --var rubric="$(cat examples/demos/langgraph_issues_census/rubric.md)" \
  --var labels="$(cat examples/demos/langgraph_issues_census/labels.json)" \
  --var provider=azure \
  --var model="$AZURE_MODEL" \
  --var output_path=examples/demos/langgraph_issues_census/results/ledger.md \
  --var results_dir=examples/demos/langgraph_issues_census/results \
  --var fixture_path=tests/fixtures/fr1130/raw_read.json \
  --var memo_store=examples/demos/langgraph_issues_census/results/memo.sqlite \
  --token-usage
```
