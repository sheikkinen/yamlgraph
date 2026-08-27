# Diary Discourse Analysis

Disposable YAMLGraph research instrument for reading the diary corpus into an
evidence dossier. It does not write a thesis, propose feature requests, extract
implementation tasks, or modify tracked repository artifacts.

## Run

```bash
yamlgraph graph lint tmp/diary-discourse-analysis/graph.yaml
yamlgraph graph run tmp/diary-discourse-analysis/graph.yaml \
  --var corpus_dir=docs/diary \
  --var include_legacy=true \
  --var output_dir=tmp/diary-discourse-analysis \
  --full
```

The graph pins `provider: inception`, `model: mercury-2`, and low temperature
for both structured LLM stages. A full repository run reads committed
`docs/diary/*.md` files, includes committed root-level `docs/diary-*.md` files
when `include_legacy=true`, and packages the FR-884 control documents
separately instead of including them in the diary map.

## Smoke fixture

```bash
yamlgraph graph run tmp/diary-discourse-analysis/graph.yaml \
  --var corpus_dir=tmp/diary-discourse-analysis/fixtures \
  --var include_legacy=false \
  --var output_dir=tmp/diary-discourse-analysis/smoke \
  --full
```

The smoke fixture uses two tiny diary fragments so the graph shape, output
writer, and coverage reconciliation can be checked without reading the live
diary corpus.

## Outputs

Only these live outputs are written:

- `dossier.json`: full raw memoranda, batch distillations, corpus manifest,
  control documents, coverage reconciliation, and run budget.
- `dossier.md`: compact navigable index for the JSON dossier.
