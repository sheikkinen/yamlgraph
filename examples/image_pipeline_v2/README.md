# Image Pipeline v2 — Critic-Filtered Prompts (FR-879)

`generate → score → filter → render`: one LLM node (single provider
from `.env`) generates N candidate prompts; a frozen local critic (the
FR-876 3.3 M-param char model from `sheikkinen/deviant-daily`) scores
them; only the top-k survivors are rendered via Replicate z-image.

The opposite lesson of [../image_pipeline/](../image_pipeline/README.md)
(v1, unguarded M×N fan-out): here the demo IS the filter — the
rejection table shows every candidate's score, band, and verdict, and
Replicate money is spent only on survivors.

## Why a frozen critic, not an LLM judge

An LLM judging an LLM is nondeterministic, costs tokens per run, and
shares training/blindness with the generator (`model_as_trusted_peer`).
The critic is a 13 MB checkpoint: identical verdicts on every run, one
parallel forward pass (~ms), zero marginal cost, and its calibration is
pinned to a corpus SHA. It measures **style fit only** — semantics stay
with the generator, safety with the boundary.

## Setup (cross-repo)

The critic lives in `sheikkinen/deviant-daily` and must be trained once
(~13 min on Apple Silicon):

```bash
git clone https://github.com/sheikkinen/deviant-daily.git
cd deviant-daily && python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[training]"
python -m training.prepare prompts/corpus.jsonl training/data --seed 7
python -m training.train --seed 42 --steps 5000 --out training/ckpt
python -m training.score --calibrate
```

Then point the pipeline at the clone:

```bash
export DEVIANT_DAILY_DIR=~/src/deviant-daily
```

Missing clone/checkpoint/calibration fails fast with these exact
commands — there is no unfiltered rendering fallback.

## Run

```bash
yamlgraph graph run examples/image_pipeline_v2/graph.yaml \
  --var style="dark fantasy, baroque, chiaroscuro" \
  --var n_candidates="10" --var top_k="3" --full
```

| Variable | Description | Default |
|----------|-------------|---------|
| `style` | Art style brief for candidate generation | `"dark fantasy"` |
| `n_candidates` | Candidates generated and scored | `"10"` |
| `top_k` | Survivors rendered (Replicate spend cap) | `"3"` |

**Provider:** resolved from the environment (`PROVIDER` in `.env`) —
the graph and prompt files contain no `provider:`/`model:` overrides.

## Scoring semantics

Per candidate: per-char NLL under the critic (register prefix applied,
input truncated to the model's 256-char context — recorded as
`truncated`), band verdict against per-register calibration
(`too_likely | in_band | too_unlikely`), plus the deviant-daily
generation boundary (redaction / 8-gram novelty / shape). `verdict:
pass` requires in_band AND boundary pass; survivors are the k lowest
NLLs among passes. Zero survivors fails the run explicitly.

Known limits (measured, FR-879 R-1): the NLL band cannot detect
memorization (verbatim corpus rows score in_band) — novelty is the
8-gram boundary's job; characters outside the training vocabulary are
skipped during scoring (e.g. non-Latin scripts are scored only on
their known-char subset).

## Outputs

```
outputs/image_pipeline_v2/{timestamp}/
├── rejection-table.md         # sanitized: hashes, scores, verdicts (committable)
├── rejection-table-local.md   # full prompt text (LOCAL ONLY, never commit)
├── zimage_NN_*.png            # survivors only
└── zimage_NN_*.txt            # sidecar when exiftool is absent (v1 contract)
```

Image metadata inherits v1's contract: best-effort EXIF via exiftool,
sidecar `.txt` fallback otherwise.

Governing FR: `feature-requests/FR-879-image-pipeline-v2-critic-filter.md`
+ judgement. Evidence from the witnessed run: [evidence/](evidence/).
