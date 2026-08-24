# Feature Request: FR-876 Minimal LLM Training Demo — deviant-daily Prompt Corpus as Training Source

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 1–2 days
**Requested:** 2026-08-24
**First consumer / first event:** the operator, at the moment of
demonstrating "how LLM training actually works" end-to-end on real,
owned, already-redacted data — first event: running
`python training/train.py` in `sheikkinen/deviant-daily` and watching
val loss fall while periodic samples visibly acquire the corpus style.
Second (deferred, NOT this FR's justification) consumer: `draw_prompt()`
falling back to a generator on `CorpusExhausted` — at ~3 posts/day the
5,893-row corpus depletes in years, so exhaustion is a real but distant
event; claiming it as first consumer would be `growth_as_default`.

## Summary

Build a minimal, from-scratch LLM training and prompt-generation system
using `sheikkinen/deviant-daily`'s `prompts/corpus.jsonl` (5,893
image-generation prompts, ~2.38 M chars ≈ 600 K tokens) as the training
source: a Markov baseline, a nanoGPT-style char-level transformer, and a
generation boundary that re-applies the corpus redaction policy and a
novelty floor to every sample. The deliverable is a teaching artifact
whose evaluation is a rejection-statistics table per rung — a visible
demonstration of what training buys.

## Value Statement

The operator gets a working, inspectable demonstration of every LLM
training mechanic (tokenization, dataset, attention, loss curve,
sampling, memorization, boundary validation) in ~350 lines on data they
own, trained in minutes on a MacBook.

## Problem

"LLM training" is understood here only at the consumer level (providers,
fine-tune APIs). There is no owned artifact demonstrating the mechanics
from scratch. The deviant-daily corpus is unusually well suited:

- **Grounded facts (read 2026-08-24, `tmp/deviant-daily/corpus.jsonl`):**
  5,893 rows, ~600 K tokens, median 49 words/prompt, max 3,690 chars.
  Two distinct registers: ~2,300 booru/tag-heavy rows
  (`underscore_tags, comma, comma…`) and ~3,600 em-dash prose rows.
  1,937 rows carry `source_file: "unknown"`.
- The style is so distinctive that a tiny model's learning is visible to
  the naked eye — `read_raw_output_first` is the native eval.
- The corpus is already sanitized at the extraction boundary
  (`scripts/extract_corpus.py`: LoRA syntax stripped, NAME/TERM
  blocklists, path/token/email scans, dedup) and is public by design —
  a model trained on it is exactly as public as its data.

600 K tokens is far too small to train a *good* LM. It is ideal for a
*demonstration* — that asymmetry is the point, and the FR must not
drift toward quality goals the data cannot support.

## Raw Output Read

- **Samples read (R-1):**
  `sheikkinen/deviant-daily@30bf8c1a5ae66df8374bf3ba0d366138af83cb15:prompts/corpus.jsonl`,
  rows 1–5 read in full 2026-08-24. Stats verified against that
  committed file with
  `python3 -c "import json;rows=[json.loads(l) for l in open('prompts/corpus.jsonl')];print(len(rows),sum(len(r['prompt']) for r in rows),sum(1 for r in rows if r['source_file']=='unknown'))"`
  → 5,893 rows / 2,384,581 prompt chars / 1,937 `unknown` source ids.
- **What I saw:** row 1 is a rotting-patriot Marvel pastiche
  whose parenthetical tag list mixes render-pipeline vocabulary
  (`vfx_render, game_asset, no_watermark`) into the aesthetic tags — a
  generator must learn that register mixing, not just English. Row 3
  embeds markdown emphasis (`*memento mori*`) inside a prompt —
  shape-gate design must not assume plain text.
  `sheikkinen/deviant-daily@30bf8c1:tools/corpus.py:18-30` documents
  that the 1,937 `unknown` rows would share one dedup key and are
  therefore content-hashed (`unknown-<sha1[:12]>`) — the exact id
  scheme generated prompts should reuse.

## Ideal Result

A stranger clones deviant-daily, runs three commands (extract-dataset,
train, generate), and in under 30 minutes on a laptop has: a loss curve,
a temperature-sweep sample sheet, a rejection-statistics table
contrasting Markov vs transformer, and N novel prompts that pass the
same redaction policy the corpus itself passed — understanding, from
code they can read in one sitting, every stage between raw text and a
sampled token.

## Proposed Solution

Host in **`sheikkinen/deviant-daily`** under `training/` (data and the
eventual consumer live there; the repo is public with redacted data;
precedent for governing deviant-daily work from a yamlgraph FR:
FR-862, FR-863). No yamlgraph-core changes.

**Rung 0 — Markov baseline** (`training/markov.py`, ~50 lines, stdlib
only): word-level trigram chain. Purpose: the baseline that makes the
neural rung measurable; demonstrates generation = next-token prediction.

**Rung 1 — char-level transformer from scratch**
(`training/model.py` + `training/train.py`, ~300 lines, PyTorch/MPS):

- Tokenizer: char-level, vocab ≈ 100 (underscore-tag morphology is
  learnable at char level; skips BPE complexity).
- Dataset: one prompt per document, `\n<|end|>\n` separator, 95/5
  train/val split. Conditioning prefix `<tag>`/`<prose>` classified
  mechanically (≥8 commas AND `_` present) — conditional generation for
  one line of code.
- Model: 4 layers, 4 heads, d=256, block 512 → ~3–5 M params; 10–30 min
  on M-series. Expected: char-level val loss ~4.6 → ~1.2 with periodic
  samples printed during training.
- Sampling (`training/generate.py`): temperature + top-k, stop at
  `<|end|>`; temperature sweep artifact (0.5 / 0.8 / 1.2).

**Generation boundary** (`training/boundary.py`) — the model's output
is a claim, not a prompt; normalize at the boundary:

1. Re-apply the extraction redaction policy (import the blocklist
   regexes and SCAN_PATTERNS from `scripts/extract_corpus.py` — one
   source of truth, no copy) — extraction-time filtering does not
   transfer; a model can recombine tokens into excluded content.
2. Novelty floor: reject any sample sharing a verbatim 8-gram (word
   level) with the training set — small models memorize small corpora;
   the regurgitation-rate-vs-temperature curve is itself a demo output.
3. Shape gates: 100–800 chars, non-empty, no truncation mid-word.

**Boundary covers every persisted sample (R-2):** `train.py`,
`generate.py`, and `eval.py` route ANY sample written to stdout, logs,
markdown, or committed artifacts through `training/boundary.py` first.
Rejected samples are counted by reason; their raw text is never
persisted.

**Dependency freeze (R-3):** PyTorch enters ONLY as a `training`
optional extra in `pyproject.toml`; a base-install import probe proves
the publish modules import without `torch`; no publish workflow
installs the extra.

**Evaluation = rejection statistics per rung** (`training/eval.py`):
for 200 samples per rung × temperature, a table of pass / redaction-hit
/ novelty-hit / shape-hit — the table is the demonstration. Coherence
is NOT a mechanical claim (R-5): any coherence observation lives in an
explicitly non-gating human-read sample note, never in a gate.

```bash
# The three commands (ideal-result path)
python training/prepare.py prompts/corpus.jsonl training/data/
python training/train.py --steps 5000 --out training/ckpt/
python training/generate.py --ckpt training/ckpt/ --n 20 --temp 0.8
```

## Acceptance Criteria

Superseded by the judgement's revised AC-01..AC-13
(`feature-requests/FR-876-minimal-llm-training-demo.judgement.md`) —
the judgement list is binding. Key deltas from the original list:

- AC-05 (was AC-02): training witness is reproducible — `--seed`,
  deterministic split, logged device/params/hyperparams/wall-clock/git
  SHA; the threshold (val loss < 1.5 within 30 min) fails the FR if
  missed, never silently lowered (R-4).
- AC-06 (was AC-03): sample sheets contain only boundary-passing or
  policy-redacted entries (R-2).
- AC-08: rejected raw text is proven (by test) not to persist into
  sample/eval artifacts (R-2).
- AC-11: `training` optional extra + base-install import probe (R-3).
- AC-13: any need to touch `tools/corpus.py`, `draw_prompt()`, publish
  workflows, or graph/prompt YAML stops enforcement for a separate FR.

## Alternatives Considered

- **Rung 2 (LoRA fine-tune of a 0.5–1B open model via mlx-lm):**
  production-plausible quality and the pretraining-vs-fine-tuning
  contrast — deferred; it teaches a different lesson (adaptation, not
  mechanics) and doubles scope. Add later as its own FR if the
  generator is ever promoted to a `draw_prompt()` fallback.
- **Host in yamlgraph `examples/demos/`:** rejected — the corpus and
  its consumer live in deviant-daily; hosting here would embed another
  repo's data concern (`where_is_the_repo_boundary`) and this repo's
  demo-gate ceremony buys nothing for a plain-Python teaching script.
- **Train on raw signed.log:** rejected — redaction happened at
  extraction for a reason; the trained model is as public as its data.
- **BPE tokenizer from scratch:** optional second lesson, cut for
  minimality; char-level suffices and is more readable.
- **A yamlgraph graph for the training loop:** rejected — the loop is a
  plain script (`is_this_a_graph`: no per-item LLM judgement, no
  fan-out). A graph shape appears only if an LLM-judge QA stage over
  generated samples is added later.

## Prior Art Disposition

**Prior art:** FR-277 (REJECTED — watcher2 baseline checkpointing: state
reuse across pipeline runs, no model training; keyword overlap only, its
rejection rationale concerns checkpoint invalidation complexity and does
not touch this territory); 020-soup-generator (SOUP/IEC-62304 doc
pipeline consuming LLMs, not training one; no overlap);
FR-666 (adversarial content-audit demo about judging LLM output, not
training — its `model_as_trusted_peer` lesson is inherited here as the
generation-boundary design, not re-implemented); 036-map-subgraph-subnodes
(map-node agent support, unrelated). None constrains or duplicates
training a model from the deviant-daily corpus.

- **FR-857 (corpus-analysis fan-out, PARKED):** analysis of corpora via
  LLM map nodes — different verb (analyze vs train); no overlap.
- **FR-826 (deviant-daily repo) / FR-862 (dispatch):** established the
  corpus, its redaction policy, and the precedent of governing
  deviant-daily changes from yamlgraph FRs. This FR extends, not
  re-litigates.
- **020-soup-generator / 034-novel-generator:** LLM-consumer demos, not
  training; no overlap.

## Related

- `sheikkinen/deviant-daily`: `prompts/corpus.jsonl`,
  `scripts/extract_corpus.py`, `tools/corpus.py`
- feature-requests/FR-826-deviantart-daily-repo.md (corpus origin,
  redaction policy C-4)
- feature-requests/FR-862-deviant-daily-on-demand-publish.md (precedent:
  yamlgraph FR governing deviant-daily)
- Reflection recorded in session 2026-08-24 (corpus stats, three-rung
  ladder, boundary design)

## Decisions (operator, 2026-08-24)

1. **Host repo:** deviant-daily `training/` — confirmed.
2. **PyTorch dependency:** approved as a `training` extra only; never
   imported by the publish pipeline.

## Implementation Status (2026-08-24)

Enforced in `sheikkinen/deviant-daily` (cloned at judged SHA 30bf8c1,
sibling dir — C-3 honored). Commits: RED 24e081a (26-test witness
suite), GREEN 830ccca (`training/` package + `training` extra; full
suite 154 passed), docs 5c0c8c2, evidence 3e05633.

**Training witness (AC-05):** seed 42, MPS, 3,299,328 params, vocab
145, block 256, batch 32, 5000 steps; val loss 5.1227 → **1.0175** in
**764.7 s** (12.7 min) — gate < 1.5 / 30 min passed with margin. Log:
`training/evidence/train-run.log` (git SHA + full config in header).
Periodic samples boundary-filtered (R-2); the step-4250 sample was
rejected `novelty:shared_8gram` — memorization onset caught live.

**Sample sheets (AC-06):** `training/evidence/samples-t{0.5,0.8,1.2}.md`
with per-sample read notes. Regurgitation-vs-temperature confirmed:
t0.5 → 6/20 attempts novelty-rejected; t0.8 → 0 (sweet spot); t1.2 →
word salad with intact syntax skeleton.

**Prediction falsified by data:** the FR guessed "Markov fails novelty
rarely" — measured: **167/200 novelty rejections** for the trigram
baseline. A trigram chain can only follow observed transitions, so its
outputs are corpus-8-gram mosaics. The rejection table demonstrates
training's value in the opposite direction from the author's intuition
— honest evaluation working as designed.

**Deviations (recorded, all within scope):**
- `pip install -e .` was broken at 30bf8c1 (flat-layout autodiscovery
  error, upstream) — AC-11's installable extra required a minimal
  `[build-system]`/`[tool.setuptools] packages` fix in pyproject.
- Mid-word truncation is generation-time truth: `boundary.check(...,
  ended=)` flag set by the sampler (token budget elapsed without
  `<|end|>`); text-only detection would be a dishonest heuristic. The
  RED test was updated with rationale before GREEN.
- Module named `training/evaluate.py` (judgement D-2 wrote `eval.py`;
  same deliverable, avoids the `eval` builtin name).
- Corpus 30bf8c1 has vocab 145 (unicode chars) vs the estimated ~100 —
  no design impact.
