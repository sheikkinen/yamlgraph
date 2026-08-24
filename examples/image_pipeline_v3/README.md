# Image Pipeline v3 — Local Model as Prompt Generator (FR-881)

The inversion of [image_pipeline_v2](../image_pipeline_v2/): v2 has a
frontier LLM propose prompts and a frozen local critic judge them; v3
has the **trained local model propose the prompts itself** — there is
no `llm` node anywhere in this graph. Prompt generation runs fully
offline; the only paid, networked step is rendering the survivors via
Replicate z-image.

```
START → sample_candidates (deviant-daily model, --json subprocess)
      → save_report      (sanitized + local tables, outputs/image_pipeline_v3)
      → generate_images  (Replicate z-image, first top-k passers only)
      → END
```

## Cross-repo setup

The generator lives in the sibling repo `sheikkinen/deviant-daily`
(built and witnessed by yamlgraph FR-876):

```bash
git clone https://github.com/sheikkinen/deviant-daily.git
cd deviant-daily && python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[training]"
python -m training.prepare prompts/corpus.jsonl training/data --seed 7
python -m training.train --seed 42 --steps 5000 --out training/ckpt   # ~13 min on MPS
```

Missing clone/venv/checkpoint/corpus fails fast with these commands —
there is deliberately **no LLM fallback** (judgement C-4): the demo's
point is that no LLM is needed.

## Run

```bash
export DEVIANT_DAILY_DIR=~/src/deviant-daily
export REPLICATE_API_TOKEN=...   # only the render step needs a credential
yamlgraph graph run examples/image_pipeline_v3/graph.yaml \
  --var start="tom of sweden, " --var top_k="3" --full
```

Graph variables: `start` (seed text the model continues; default empty),
`cond` (`tag`|`prose`), `temp` (default 0.8 — the witnessed sweet spot),
`seed`, `n_candidates` (default 10), `top_k` (default 3).

## Selection and privacy boundary

- Selection is exactly the **first top-k boundary-passing candidates in
  generation order** — no NLL ranking, no scorer, no LLM judge
  (judgement AC-06). The generation boundary (redaction re-scan, 8-gram
  novelty floor, shape gates) already gated every candidate inside the
  generator.
- Rejected raw text never leaves the generator — reports carry
  rejection *counts* only. The sanitized `generation-table.md` (no
  prompt text) is committable; `generation-table-local.md` (full text)
  stays local.
- Reports carry `ckpt_sha`/`corpus_sha`/`git_sha` provenance stamps.

## Known limits

The generator is a 3.3 M-param char model trained on ~600 K tokens: it
writes in-register prompt *style*, not meaning. Expect surreal
recombinations; the boundary and `top_k` are the quality controls, and
temperature is the creativity dial (see the FR-876 sample sheets in
deviant-daily `training/evidence/`).

Evidence from the witnessed demo run lives in [evidence/](evidence/).
