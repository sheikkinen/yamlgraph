# ICPC-2 RFE Classifier (FR-722)

Classifies a freeform encounter transcription into ICPC-2 **Reason for
Encounter** code(s) with titles, verdicts, and short reasoning.

Architecture: cluster map fan-out → per-cluster LLM verdicts → fully
deterministic python reducer.

```
transcript ──► load_catalog ──► map: 33 clusters (17 chapters × C1/C7)
                                  └─ reason_cluster (only LLM judgement)
                              ──► reduce (python: rank, dedup, validate)
                              ──► classification + meta
```

## Setup — generate the catalog first (required)

The ICPC-2 rubric data is **© Wonca** and is never committed to this
repository. You download it yourself, under your own acceptance of the
[Wonca licensing terms](http://www.ph3c.org/4daction/w3_CatVisu/en/rules-%26-ethics.html?wCatIDAdmin=1101),
from the official WICC-delegated repository (Norwegian Directorate of
Health):

```bash
# 1. Download ICPC-2e-v7.0 (the builder prints the URL if absent)
python examples/icpc-2-rfe/nodes/build_catalog.py
# → verifies sha256, parses ClaML, writes data/icpc2_rfe_catalog.yaml
#   (686 rubrics, gitignored)
```

## Run

The runner classifies a transcript file (or stdin) and prints only the
answer — the full state dump goes to `logs/icpc2-rfe-last-run.log`:

```bash
examples/icpc-2-rfe/classify.sh examples/icpc-2-rfe/data/HP-36-acting-on-behalf-of-adult.md

echo "Patient calls because of a dry cough for two weeks, worse at night." \
  | examples/icpc-2-rfe/classify.sh
```

```
PRIMARY
  A13  Concern about/fear of medical treatment  [match, 0.98]
      The caller is requesting renewal of a blood pressure medication ...
      evidence: "Haluaisin uusia hänen verenpainelääkereseptinsä."; ...
SECONDARY
  K86  Hypertension uncomplicated  [match, 0.98]
  ...
coverage: ICPC-2e-v7.0, components [1, 7], 33 clusters, 34 candidates
```

Raw invocation (prints the entire graph state — large):

```bash
yamlgraph graph run examples/icpc-2-rfe/graph.yaml \
  --var transcript="Patient calls because of a dry cough for two weeks, worse at night." \
  --full 2>/dev/null | python3 examples/icpc-2-rfe/nodes/show_result.py
```

Output (state keys `classification` + `meta`):

```yaml
classification:
  primary:   {code: R05, title: Cough, verdict: match, confidence: 0.99, ...}
  secondary: []          # multi-label when justified
  low_confidence: false  # true + best_partial when nothing reaches "match"
  best_partial: [...]
meta:
  catalog_version: ICPC-2e-v7.0
  catalog_coverage: {components: [1, 7], clusters_evaluated: 33}
```

## Contracts (enforced by tests, `tests/unit/test_fr722_icpc2_rfe.py`)

- **Evidence honesty**: the model's `evidence_spans` are claims — the
  reducer aligns each claim to the transcript and outputs the verbatim
  transcript substring (near-miss ≥ 0.85 similarity is repaired;
  anything below is a fabrication and fails the run). LLM quoting is
  fragile; copying is done in code.
- **Catalog honesty**: candidate codes must exist in the catalog;
  `meta.catalog_coverage` makes "no match" interpretable (components
  2–6 process codes are phase 2).
- **Deterministic ranking**: verdict rank → confidence → code; per-code
  dedup keeps the best-ranked occurrence; no reducer LLM call.
- **Provenance**: every generated row is `verified` with
  `source_reference: ICPC-2e-v7.0/<code>`; hand-added rows are
  `provisional` and excluded unless `--var include_provisional=1`.

## Assumptions / limits (phase 1)

- English prompting only; RFE-centric (not diagnosis coding).
- Confidence values are uncalibrated — used only to tie-break within a
  verdict rank, never compared across ranks.
- The committed `data/fixture_catalog.yaml` is a paraphrased 5-row
  test fixture, not clinical data.
