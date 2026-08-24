# Judgement: FR-876 Minimal LLM Training Demo — deviant-daily Prompt Corpus as Training Source

**Verdict:** APPROVED WITH REVISIONS — the teaching artifact is real, scoped to the right repository, and strategically a contrib/example, but authority activates only after the FR fixes input-closure evidence, closes the raw-sample publication leak, freezes the optional PyTorch dependency boundary, and makes the training/evaluation witnesses reproducible.

**Reviewed against:** `feature-requests/FR-876-minimal-llm-training-demo.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.judgement.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.judgement.md`; `feature-requests/FR-277-watcher2-baseline-checkpointing.md`; `feature-requests/FR-666-the-beasts-number-adversarial-content-audit.md`; `feature-requests/FR-857-corpus-analysis-fanout-graph.md`; `feature-requests/020-soup-generator.md`; `feature-requests/034-novel-generator-demo.md`; `feature-requests/036-map-subgraph-subnodes.md`; cited target repo `sheikkinen/deviant-daily@30bf8c1a5ae66df8374bf3ba0d366138af83cb15`: `prompts/corpus.jsonl`, `scripts/extract_corpus.py`, `tools/corpus.py`, `README.md`, `pyproject.toml`, `graph.yaml`, `tools/steps.py`.

## What is sound

The first consumer and first event are concrete: the operator wants to demonstrate from-scratch LLM training on owned, already-redacted data by running `python training/train.py` in `sheikkinen/deviant-daily` and watching validation loss and samples change (`feature-requests/FR-876-minimal-llm-training-demo.md:8-16`). That is a real teaching event, not the deferred `draw_prompt()` exhaustion fallback, which the FR correctly refuses to use as its first-consumer claim (`feature-requests/FR-876-minimal-llm-training-demo.md:13-16`).

The strategic classification is **Contrib/example**. The FR explicitly hosts the work in `sheikkinen/deviant-daily`, keeps yamlgraph core unchanged, and treats the artifact as a plain-Python training demonstration rather than a framework primitive (`feature-requests/FR-876-minimal-llm-training-demo.md:82-88`, `174-177`). That aligns with repo doctrine's `where_is_the_repo_boundary` warning that committed state must not embed another repo's working tree (`.github/copilot-instructions.md:87`, `131`) and with the precedent that deviant-daily work may be governed here while implemented in the sibling repo (`feature-requests/FR-826-deviantart-daily-repo.md:5-11`; `feature-requests/FR-862-deviant-daily-on-demand-publish.judgement.md:53-65`).

The corpus and boundary premise are supported by committed target-repo evidence. The target README records 5,893 kept prompts, public approval, redaction policy, and the claim that raw unsanitized data never leaves the operator's machine (`sheikkinen/deviant-daily@30bf8c1:README.md:23-36`). The extraction script defines the public blocklists and scan patterns the FR wants to reuse (`sheikkinen/deviant-daily@30bf8c1:scripts/extract_corpus.py:27-43`) and emits only `{"prompt": ..., "source_file": ...}` rows after sanitization, dedup, and scans (`sheikkinen/deviant-daily@30bf8c1:scripts/extract_corpus.py:111-143`). The runtime corpus helper confirms the `unknown-<sha1[:12]>` id rule for missing source ids (`sheikkinen/deviant-daily@30bf8c1:tools/corpus.py:18-30`). The raw corpus itself corroborates the distinctive mixed register cited by the FR: row 1 mixes prose with tag vocabulary such as `vfx_render`, `game_asset`, and `no_watermark`, and row 3 includes markdown emphasis inside the prompt (`sheikkinen/deviant-daily@30bf8c1:prompts/corpus.jsonl:1-3`; `feature-requests/FR-876-minimal-llm-training-demo.md:58-70`).

The architecture is mostly minimal for the stated lesson. A stdlib Markov baseline plus a small char-level transformer makes the next-token-training contrast visible without adding provider APIs, BPE, LoRA, or YAMLGraph orchestration (`feature-requests/FR-876-minimal-llm-training-demo.md:89-107`, `161-177`). The generation boundary also follows the repo's boundary doctrine: model output is treated as a claim and normalized before use (`feature-requests/FR-876-minimal-llm-training-demo.md:108-119`; `.github/copilot-instructions.md:49-52`, `115-116`).

The prior-art disposition is adequate in direction. **Prior art:** FR-277 is about watcher2 state reuse and imports/exports, not model training (`feature-requests/FR-277-watcher2-baseline-checkpointing.md:12-18`, `127-140`); FR-666 demonstrates deterministic gates over LLM output, not training (`feature-requests/FR-666-the-beasts-number-adversarial-content-audit.md:9-15`, `74-83`); FR-857 is a parked corpus-analysis graph, not a trainer (`feature-requests/FR-857-corpus-analysis-fanout-graph.md:1-4`, `14-28`); 020 and 034 are LLM-consumer demos, not training systems (`feature-requests/020-soup-generator.md:9-13`; `feature-requests/034-novel-generator-demo.md:35-49`); and 036 concerns map subgraph support rather than training (`feature-requests/036-map-subgraph-subnodes.md:145-176`). FR-876-minimal-llm-training-demo.md is the FR under judgement, not prior art.

## Required revisions

### R-1: Replace local tmp evidence with committed target-repo citations

Revise the Raw Output Read so it cites committed target-repo evidence, not `tmp/deviant-daily/corpus.jsonl`. Judge doctrine permits only committed artifacts, cited evidence, and repo doctrine; uncommitted working notes are outside input closure (`.github/skills/judge-fr/doctrine.md:16-24`). The current FR says the raw read came from `tmp/deviant-daily/corpus.jsonl` (`feature-requests/FR-876-minimal-llm-training-demo.md:58-61`), while the committed evidence actually lives at `sheikkinen/deviant-daily@30bf8c1:prompts/corpus.jsonl` and related target files.

Fold this mechanically by replacing the tmp path with an immutable target-repo commit SHA, listing the exact files and line/sample references used for corpus facts, and recording the stats command or artifact that proves 5,893 rows, 2,384,581 prompt characters, and 1,937 `unknown` source ids. Keep the concrete surprising sample observations; attach them to committed JSONL row numbers or a committed evidence artifact.

### R-2: Gate every persisted generated sample, including training logs

Revise the sample/log contract so no raw model output can be committed before the redaction and novelty boundary runs. The FR correctly says generated output is a claim and extraction-time filtering does not transfer (`feature-requests/FR-876-minimal-llm-training-demo.md:108-117`), but it also requires a committed training run log with periodic samples (`feature-requests/FR-876-minimal-llm-training-demo.md:102-104`, `136-139`) and a committed sample sheet (`feature-requests/FR-876-minimal-llm-training-demo.md:140-143`). Those artifacts can expose unfiltered recombinations unless the boundary covers them explicitly.

Fold this by requiring `train.py`, `generate.py`, and `eval.py` to pass any sample that is written to stdout, logs, markdown, or committed artifacts through `training/boundary.py`. Rejected samples may be counted by reason, but their raw text must not be persisted unless redacted by the same policy. Add tests proving an excluded NAME hit, TERM hit, scan-pattern hit, verbatim-row hit, 8-gram hit, too-short hit, too-long hit, and mid-word truncation are not written into sample-sheet or eval artifacts.

### R-3: Freeze the training dependency and import boundary

Revise the implementation surface to specify the dependency change. The FR records an operator decision that PyTorch is approved as a `training` extra only and must never be imported by the publish pipeline (`feature-requests/FR-876-minimal-llm-training-demo.md:212-216`), but its acceptance criteria do not require a `pyproject.toml` change or a guard that normal deviant-daily installs remain publish-only. The current target repo has only base dependencies and a `dev` extra (`sheikkinen/deviant-daily@30bf8c1:pyproject.toml:1-16`); the publish graph and steps already run without PyTorch (`sheikkinen/deviant-daily@30bf8c1:graph.yaml:14-39`; `sheikkinen/deviant-daily@30bf8c1:tools/steps.py:23-39`).

Fold this by authorizing exactly a `training` optional extra for PyTorch and any training-only dependencies. Add a test or import probe proving `pip install -e .` can import and run the existing publish modules without importing `torch`, while `pip install -e ".[training]"` is the documented path for `training/train.py`. Do not add PyTorch to base dependencies or GitHub Actions publish workflows.

### R-4: Make the training witness reproducible and bounded

Revise AC-02 so the enforcer can produce and evaluate the loss witness without relying on ambient luck. The current criterion requires val loss `< 1.5` within 30 minutes on the operator's machine (`feature-requests/FR-876-minimal-llm-training-demo.md:136-139`), but it does not freeze seed, split identity, device fallback, logged hyperparameters, or failure semantics. Judge doctrine requires mechanically checkable acceptance criteria and tests derivable from them (`.github/skills/judge-fr/doctrine.md:43-45`, `58-61`).

Fold this by requiring deterministic dataset split and dataloader seeding, explicit `--seed`, logged device (`mps|cpu`), parameter count, block size, batch size, steps, train/val counts, initial loss, final loss, wall clock, and git SHA. The committed training witness may be non-CI, but unit tests must cover tokenizer encode/decode, dataset separator handling, split determinism, model forward shape, and one tiny overfit smoke run that completes quickly on CPU. The full evidence run must fail the FR if it misses the frozen loss threshold or timeout; do not silently lower the bar after observing the result.

### R-5: Remove subjective evaluation claims or bind them to a real metric

Revise the evaluation section so it does not claim unmeasured coherence. The FR says Markov "fails novelty rarely and coherence always" while the proposed table only measures pass, redaction-hit, novelty-hit, and shape-hit (`feature-requests/FR-876-minimal-llm-training-demo.md:120-123`). Coherence is not otherwise defined, and doctrine rejects aspirational acceptance criteria that cannot be checked mechanically (`.github/skills/judge-fr/doctrine.md:43-45`).

Fold this by either deleting the coherence claim or adding a separate, explicitly non-gating human-read sample note. The authorized mechanical evaluation is the rejection-statistics table per rung and temperature. If coherence becomes a gate, it needs its own rubric, samples, and acceptance threshold in a separate FR or a revised judgement pass.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-876-minimal-llm-training-demo.md` folding R-1 through R-5 |
| D-2 | Sibling repo `sheikkinen/deviant-daily`: `training/prepare.py`, `training/markov.py`, `training/model.py`, `training/train.py`, `training/generate.py`, `training/boundary.py`, `training/eval.py` |
| D-3 | Sibling repo `sheikkinen/deviant-daily`: `training/README.md` and committed non-secret evidence artifacts for training log, temperature sample sheet, and rejection-statistics table |
| D-4 | Sibling repo `sheikkinen/deviant-daily`: tests for Markov determinism, tokenizer/dataset/model smoke behavior, generation stop/conditioning, boundary redaction/novelty/shape rejection, eval table rendering, and dependency/import boundary |
| D-5 | Sibling repo `sheikkinen/deviant-daily`: `pyproject.toml` optional `training` extra only |
| D-6 | FR implementation-status update in this repo with non-secret target commit, commands, timing, and evidence artifact paths |

Not authorized: yamlgraph core/runtime changes; new or modified yamlgraph `graph.yaml` or `prompts/*.yaml` artifacts; changes to deviant-daily publishing workflow behavior, `tools/corpus.py`, or `draw_prompt()`; automatic `CorpusExhausted` fallback integration; training on raw `signed.log`; committing raw signed logs, secrets, token-bearing logs, generated model checkpoints, generated images, or unfiltered rejected samples; adding PyTorch to deviant-daily base dependencies or publish workflows; LoRA/BPE/open-model fine-tuning; LLM-judge QA over generated samples; changing judge/review/graph-authoring doctrine.

## Revised acceptance criteria

- [ ] AC-01: FR-876 is revised to cite committed target-repo evidence by immutable commit SHA and to fold R-1 through R-5 before enforcement begins.
- [ ] AC-02: `training/markov.py` implements a stdlib-only word-level trigram generator; tests prove deterministic output under a seeded RNG and no dependency on PyTorch.
- [ ] AC-03: `training/prepare.py` reads `prompts/corpus.jsonl`, assigns deterministic `<tag>`/`<prose>` prefixes by the FR's classifier, writes train/val artifacts with a seeded 95/5 split, and tests prove split stability and `<|end|>` separator handling.
- [ ] AC-04: `training/model.py` implements the char-level tokenizer and transformer; tests cover encode/decode round trip, model forward output shape, and a tiny CPU overfit/smoke run.
- [ ] AC-05: `training/train.py --seed <n> --steps 5000 --out training/ckpt/` records device, parameter count, hyperparameters, train/val counts, initial loss, final loss, wall clock, and git SHA; the committed evidence log shows final validation loss `< 1.5` within 30 minutes on the operator's machine.
- [ ] AC-06: `training/generate.py` stops at `<|end|>`, honors `<tag>` and `<prose>` conditioning, supports temperature/top-k, and emits a committed temperature-sweep sample sheet at 0.5, 0.8, and 1.2 containing only boundary-passing or policy-redacted entries with per-sample read notes.
- [ ] AC-07: `training/boundary.py` imports NAME/TERM blocklists and `SCAN_PATTERNS` from `scripts/extract_corpus.py` without duplicating regexes; tests witness rejection for each blocklist/scan category.
- [ ] AC-08: Novelty checking rejects a verbatim training row and any generated sample sharing a word-level 8-gram with the corpus; tests cover both cases and prove rejected raw text is not persisted to sample/eval artifacts.
- [ ] AC-09: Shape gates reject empty samples, samples outside 100-800 characters, and samples truncated mid-word; tests cover each failure mode.
- [ ] AC-10: `training/eval.py` produces a markdown rejection-statistics table for Markov versus transformer at 200 samples per rung and temperature, with pass/redaction-hit/novelty-hit/shape-hit counts; a smaller test fixture proves table rendering without running the full training job.
- [ ] AC-11: `pyproject.toml` adds PyTorch only under a `training` optional extra; a base-install import probe proves existing publish modules import without `torch`, and the training README documents `pip install -e ".[training]"`.
- [ ] AC-12: `training/README.md` documents the three-command path, the demo-not-quality honesty note for the ~600 K-token corpus, public-data provenance, checkpoint/artifact hygiene, and the rule to train only on the redacted committed corpus, never raw `signed.log`.
- [ ] AC-13: No deviant-daily changes modify `tools/corpus.py`, `draw_prompt()`, publish workflows, existing `graph.yaml`, or existing YAML prompts; if enforcement discovers those changes are necessary, stop for a separate FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-876-minimal-llm-training-demo.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | The sibling repo boundary is hard: do not vendor, submodule, archive, or commit `sheikkinen/deviant-daily` into this yamlgraph repository. | GATE |
| C-4 | All generated text persisted in logs, sample sheets, eval artifacts, README examples, or FR updates must pass `training/boundary.py` or be policy-redacted; raw rejected samples must not be committed. | GATE |
| C-5 | Training may use PyTorch only through the optional `training` extra and must not alter the existing publish pipeline's base dependency or workflow install path. | GATE |
| C-6 | If implementation requires yamlgraph core/runtime changes, graph/prompt authoring, `draw_prompt()` integration, raw `signed.log` access, LoRA/BPE/open-model fine-tuning, or an LLM-judge QA stage, stop for a separate FR. | GATE |

Authority granted: after the required revisions are folded, enforcement may build the minimal Markov-plus-char-transformer training demo, generation boundary, rejection-statistics evaluation, tests, optional training dependency, README, and non-secret evidence artifacts in the separate `sheikkinen/deviant-daily` repository within the frozen scope above.
