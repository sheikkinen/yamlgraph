# Feature Request: FR-881 Image Pipeline v3 — Trained Local Model as Prompt Generator

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Requested:** 2026-08-24
**Effort:** 0.5–1 day
**Depends on:** FR-879 (in flight — v2 critic-filter pipeline; shares
`DEVIANT_DAILY_DIR` wiring, report shape, and z-image render node)
**First consumer / first event:** the operator (sheikkinen), the first
run after FR-879 lands: one command generates 10 candidate prompts
**from the FR-876 trained 3.3 M-param local model** (zero LLM API
cost, zero network for generation), boundary-filters them, renders the
survivors via Replicate z-image — the full loop from "corpus of old
prompts" to "new images in the corpus's own voice" with the only paid
step being the render.

## Summary

A sibling of `examples/image_pipeline_v2` that swaps the generator:
v2 is *frontier LLM proposes, local model disposes*; v3 is *local
model proposes, boundary disposes* — the FR-876 trained model becomes
the prompt SOURCE for the 10 candidates, sampled at the witnessed
sweet spot (t0.8, 165/200 pass), filtered by its own generation
boundary, top-k rendered via z-image. Together v1/v2/v3 complete the
example triptych: unguarded fan-out / LLM-generator + local-critic /
local-generator + mechanical gate.

## Value Statement

The operator gets style-true images whose prompt generation costs
nothing and leaks nothing (fully offline until the render step), and
yamlgraph gains the missing third example shape: a self-hosted
generative model inside a graph, with the trust inverted — the
mechanical boundary, not any LLM, is the judge.

## Problem

- FR-876 produced a working generator (165/200 boundary-pass at t0.8,
  witnessed in `training/evidence/rejection-stats.md`) but its only
  consumer is a CLI human. The obvious next consumer — feed it to the
  existing image-render machinery — does not exist.
- FR-879's v2 spends frontier-LLM tokens to *propose* prompts in a
  style the local model already speaks natively; for corpus-style
  images that's paying twice for style fidelity the 13-minute training
  run already bought.
- The gap is small by design: v2 already builds the subprocess seam to
  deviant-daily, the report artifact, and the render node; v3 is a
  generator swap on that chassis.

## Ideal Result

`yamlgraph graph run examples/image_pipeline_v3/graph.yaml --var
start="tom of sweden, " --var top_k="3" --full` runs with no LLM API
key at all: the local model samples 10 boundary-passing candidates
(seeded, reproducible), optionally continuing an operator `--start`
seed text, a rejection table records every attempt, and only the top-k
survivors hit Replicate. Total marginal cost = k renders. A reader of
the output directory sees which prompts the model wrote, which the
boundary killed and why, and which became images.

## Proposed Solution

Two small deliverables on the FR-879 chassis (same repo boundary:
deviant-daily owns model + sampling; yamlgraph orchestrates).

**D-A: batch-generation CLI contract in `sheikkinen/deviant-daily`**
(extend `training/generate.py`, ~30 lines):

- `--json` mode: emit JSONL (`{prompt, attempts, verdict_counts,
  seed, temp, cond, start, ckpt_sha}`) instead of human text — the
  machine-readable twin of the existing CLI, stamped with checkpoint
  provenance (`artifact_carries_code_identity`).
- Honors existing `--n/--temp/--cond/--start/--seed`; no new sampling
  logic — the boundary loop already exists and is witnessed.
- Tests: JSONL shape, provenance stamp, rejected-text-never-emitted
  (R-2 inheritance) on a tiny fixture checkpoint.

**D-B: `examples/image_pipeline_v3/` in yamlgraph** — authored ONLY
via the graph-authoring sole route (`scripts/author.sh`, FR-767):

```
START → sample_candidates (python tool → subprocess: training/generate.py --json)
      → save_report (reuse v2 node — same scored/report shape)
      → generate_images (reuse v1 node — z-image, survivors only)
      → END
```

- No `llm` node in the graph at all — the demo's headline. Graph vars:
  `start` (seed text, default empty), `cond` (tag|prose, default
  prose), `temp` (default "0.8" — the witnessed sweet spot), `n_candidates`
  (default "10"), `top_k` (default "3"), `seed`.
- `sample_candidates` locates deviant-daily via `DEVIANT_DAILY_DIR`
  (same contract as FR-879's score_filter); fails fast with the train
  commands when clone/ckpt missing — no fallback to an LLM generator
  (Commandment 6: a silent LLM substitute would be a plausible wrong
  answer for a demo about NOT needing one).
- Ranking without a critic: v3 orders candidates by fewest attempts
  needed (cheap proxy), OR — if FR-879's `training/score.py`
  calibration ships first — by in-band NLL. Decide at enforce time
  based on what FR-879 has landed; record the choice in the FR.
- v1 and v2 untouched.

```bash
# The demo — no LLM key needed until the render step
export DEVIANT_DAILY_DIR=~/src/deviant-daily
yamlgraph graph run examples/image_pipeline_v3/graph.yaml \
  --var start="tom of sweden, " --var top_k="3" --full
```

## Acceptance Criteria

- [ ] AC-01: `training/generate.py --json` (deviant-daily) emits JSONL
      with prompt, verdict counts, sampling params, and ckpt SHA;
      tests witness shape, provenance, and no rejected raw text.
- [ ] AC-02: `examples/image_pipeline_v3/` authored via the sole
      authoring route with lint + smoke evidence
      (`tmp/draft-authoring-report.md`).
- [ ] AC-03: The graph contains NO `llm` node (witnessed by lint /
      graph inspection); prompt generation runs offline.
- [ ] AC-04: `sample_candidates` fails fast with actionable train/setup
      commands when `DEVIANT_DAILY_DIR`, checkpoint, or corpus is
      missing; no LLM fallback path exists.
- [ ] AC-05: Demo run evidence committed: rejection table + k rendered
      images from a `--start`-seeded run; per-sample read note in the
      enforcement record (`read_raw_output_first`).
- [ ] AC-06: v1/v2 diffs empty; shared nodes reused by import, not
      copied.

## Alternatives Considered

- **Fold into FR-879 as a graph var (`generator=llm|local`):** rejected
  — v2's judgement scope is frozen mid-enforcement; a mode switch
  doubles its test matrix and muddies its lesson (critic filtering).
  Sibling example keeps both lessons legible.
- **Serve the model behind LM Studio/OpenAI-compat and use a normal
  `llm` node:** rejected — ceremony without benefit at 3.3 M params;
  subprocess is the honest seam, and "no llm node" IS the demo.
- **Skip ranking, render first k passers:** viable minimal fallback;
  kept as the floor if both ranking options prove awkward — record the
  choice either way.
- **Wait for corpus exhaustion (the FR-876 deferred consumer):**
  orthogonal — that integration targets the daily publisher pipeline in
  deviant-daily; this FR only consumes the model inside a yamlgraph
  example.

## Prior Art Disposition

**Prior art:** FR-879 (in flight — chassis and inversion partner:
LLM-generator/local-critic vs this FR's local-generator; shares
`DEVIANT_DAILY_DIR` seam, report artifact, render node; dispositioned
as dependency, not duplicate); FR-876 (Enforced — built the generator,
boundary, and sampling CLI this FR consumes; its deferred
`draw_prompt()` integration is NOT taken up here); FR-109 (In Progress,
batch image prompt generation via LLM graph — different generator
class, superseded in this territory by the v2/v3 pair); FR-202
(image-generation pipeline origin of the z-image render node — reused,
not modified); 034-novel-generator / 020-soup-generator (LLM-consumer
demos, no overlap).

## Related

- feature-requests/FR-876-minimal-llm-training-demo.md (+ judgement) —
  the model, boundary, evidence
- feature-requests/FR-879-image-pipeline-v2-critic-filter.md (+
  judgement) — the chassis
- `sheikkinen/deviant-daily@5bd0bab:training/` — generator + evidence
- examples/image_pipeline/ (v1), examples/image_pipeline_v2/ (v2)

## Open Questions (for the human, inline)

1. **Ranking source** — fewest-attempts proxy (zero new deps) vs
   FR-879's NLL calibration (better signal, couples to its landing).
   Recommended: decide at enforce time, floor = first-k-passers. A: ___
2. **Sequencing** — enforce only after FR-879 merges (clean chassis
   reuse), or in parallel with copied nodes reconciled later?
   Recommended: after FR-879. A: ___
