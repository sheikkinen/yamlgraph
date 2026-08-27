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
  --var output_path=tmp/corpus-census-ledger.md \
  --var brief_path=tmp/census-brief.md \
  --var brief_rubric="What does this corpus cover overall?"
```

## Synthesize tail (FR-895)

The pipeline ends in a human-readable brief: `brief_path` and
`brief_rubric` are REQUIRED — `prepare_brief_input` fails loudly before
any synthesis call when either is missing. The synthesis input is bounded
(top-N ledger rows by weight) and restricted to a public-safe column
allowlist; one pinned `claude-haiku-4-5` call emits structured claim
blocks; the LLM-free citation boundary (`adapters/census_brief.py`)
validates every citation against the ledger before rendering. On
rejection NO brief is written — a `*.REJECTED.md` artifact carries the
deterministic summary head and the reasons.
