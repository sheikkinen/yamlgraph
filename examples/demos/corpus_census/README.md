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

## Judgement normalization (FR-940)

`reduce_ledger` normalizes every `judgement` at the ledger boundary —
deterministic and LLM-free: enum/tag prefix strip (`(a) `, `type: `),
cut at the first `|`/`;`/newline, quote unwrap, lowercase, then a
frozen label grammar (1–64 chars, `a-z0-9 _/&-`, ≤4 words). Values
failing the grammar are DEMOTED to `abstain` (reason
`unparseable judgement shape`) — never dropped. Optional vocabulary:

```bash
--var labels='["new-spark","reframe","steering","ops"]'
```

`labels` must be a non-empty JSON list, unique under casefold,
`abstain` reserved (violations fail the run). Matching is
case-insensitive and emits the caller's canonical spelling; misses
demote with reason `label not in vocabulary`. Every reconciliation is
recorded: JSONL rows carry `raw_judgement` (original model text,
verbatim) and `repaired`; the markdown ledger head carries
`Normalization: N repaired, M demoted, K model-abstained, F row-failed of T rows.`

## Row-level failure containment (FR-943)

One malformed model output no longer forfeits the batch. Attributable
model-owned failures become fail-closed **rows** instead of aborting
`reduce_ledger`:

1. **Map-error findings** (`_error` with a usable `_map_index`) — a
   failed branch (schema miss, timeout, provider error).
2. **Error-string judgements** (`Error:` / `No results`).
3. **Model-owned envelope validation errors** — every Pydantic error
   location rooted in `judgement`/`confidence`/`evidence_span`/
   `abstained`/`abstain_reason` (or the model-level abstention
   cross-check, `loc == ()`).

A contained row is `abstain` with `confidence 0.0`, a bounded
`row failed: …` reason (240-char cap), and the FULL causal evidence
preserved verbatim in `raw_judgement` (map-error text, original
judgement, or deterministic JSON of the whole finding). Structural
impossibilities — non-dict findings, unattributable or duplicate
indexes, reducer-owned validation failures, missing findings — remain
batch-fatal (FR-892). Taxonomy helpers live in `ledger_failures.py`.

## Model selection (FR-940)

The judge and synthesis model are caller-selectable:

```bash
--var model=mercury-2 --var provider=inception
```

Defaults (unset or empty vars) fall back to the graph `defaults:`
chain — `anthropic` / `claude-haiku-4-5`. Ledger and brief provenance
carry the effective model.
