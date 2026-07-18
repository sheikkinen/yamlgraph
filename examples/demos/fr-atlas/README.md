# FR Atlas — the project as told by its feature requests

Turns a project's `feature-requests/` corpus into a newcomer-facing
narrative: themes with arcs, member FRs with verbatim statuses, a
graveyard of rejections, and a three-paragraph story opener — so a new
person can read the project's history as a story instead of querying a
folder blind (FR-748).

## Usage

```bash
# Validate
yamlgraph graph lint examples/demos/fr-atlas/graph.yaml

# Run on this repo (writes docs/<date>-fr-atlas.md)
yamlgraph graph run examples/demos/fr-atlas/graph.yaml --var project_dir=.

# Run on any project with a feature-requests/ folder
yamlgraph graph run examples/demos/fr-atlas/graph.yaml \
  --var project_dir=projects/ninchat_voice
```

## Contract (what is judged vs what is mechanical)

| Concern | Owner | Rule |
|---|---|---|
| FR identity | code | id = filename stem, never an `FR-` regex (`070-gui-web-playground` survives) |
| Status | code | verbatim from `**Status:**` at HEAD; first-word bucket with visible `other`; headerless FRs reported, not dropped |
| Dates | code | one `git log --name-only` pass; no filesystem mtimes |
| Digest | code | title + first ~10 lines after `## Problem` (mechanical excerpt, no per-FR LLM) |
| Theme candidates | model | one judgement per ~50-FR chunk (map fan-out) |
| Theme merge | model | one judgement over candidate keys — the model never carries FR ids across the merge |
| Id claims | code | reconciled against the collected population: brackets stripped, dropped `FR-` prefix restored, shortened/paraphrased slugs repaired by unique numeric head or similarity floor (≥0.5, strict winner); ties/misses raise |
| Coverage | code | every FR exactly once; unclaimed → visible `misc`; count-in == count-out asserted |
| Story opener | model | one bounded judgement, exactly three paragraphs, grounded in the reconciled taxonomy only |
| Module axis | code | CAP registry join when `capabilities/` exists; otherwise git paths only, **loudly declared** in the header |

## Pipeline

```
START → collect (python) → theme_chunks (map/llm) → assemble (python)
      → merge_themes (llm) → finalize (python) → story_opener (llm)
      → render (python) → END
```

Three LLM judgements total; everything else is deterministic code.
`assemble` and `finalize` reconcile every model claim against the
collected population — repair within the similarity floor, reject
below it.

## How this differs from neighbours

- **`scripts/fr_board.py`** answers *what is in flight now* (pipeline
  stages, committed board). The atlas answers *what has this project
  been about* (themes, arcs, graveyard) — a fresh read each run,
  never a committed standing board.
- **A recap/summary doc** is hand-curated; the atlas is regenerated
  from the corpus and mechanically guarantees no FR is silently
  dropped or double-counted.

## Verified runs (2026-07-18)

| Corpus | FRs | Map calls | Themes | Output |
|---|---|---|---|---|
| yamlgraph | 729 (+2 companions excluded) | 15 | 13 | `docs/2026-07-18-fr-atlas.md` |
| ninchat_voice (no CAP registry) | 300 (+96 excluded) | 6 | 14 | `projects/ninchat_voice/docs/2026-07-18-fr-atlas.md` |

Economics: ≈159k input tokens (17 LLM calls) for the yamlgraph corpus,
≈64k (8 calls) for ninchat_voice — well under a dollar per run on the
default deployment.

## Files

```
fr-atlas/
├── graph.yaml            # Pipeline definition
├── demo-output.log       # Captured real run (ninchat_voice corpus)
├── nodes/
│   ├── collect.py        # Corpus → digests, chunks, module index (deterministic)
│   ├── pipeline.py       # Assemble + finalize; id reconciliation boundary
│   ├── coverage.py       # Every-FR-once enforcement
│   └── render.py         # Markdown assembly, graveyard, mechanical counts
└── prompts/
    ├── chunk_themes.yaml # Per-chunk theme candidates
    ├── merge_themes.yaml # Candidate-key merge (no FR ids)
    └── story_opener.yaml # Three-paragraph opener
```

Tests: `tests/unit/test_fr748_fr_atlas.py` (REQ-YG-566, CAP-208).
