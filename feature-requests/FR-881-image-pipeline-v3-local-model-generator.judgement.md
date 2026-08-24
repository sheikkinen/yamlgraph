# Judgement: FR-881 Image Pipeline v3 — Trained Local Model as Prompt Generator

**Verdict:** APPROVED WITH REVISIONS — the local-generator sibling example is strategically sound and mostly minimal, but authority activates only after the FR folds the FR-879 status mismatch, freezes first-k-passer semantics, defines the JSONL contract precisely, resolves v2 report reuse without wrong output paths, and replaces committed-image evidence with sanitized run evidence.

**Reviewed against:** `feature-requests/FR-881-image-pipeline-v3-local-model-generator.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; repo doctrine supplied in `.github/copilot-instructions.md` / `CLAUDE.md`; `feature-requests/FR-876-minimal-llm-training-demo.md`; `feature-requests/FR-876-minimal-llm-training-demo.judgement.md`; `feature-requests/FR-879-image-pipeline-v2-critic-filter.md`; `examples/image_pipeline_v2/graph.yaml`; `examples/image_pipeline_v2/README.md`; `examples/image_pipeline_v2/nodes/score_filter.py`; `examples/image_pipeline_v2/nodes/save_report.py`; `examples/image_pipeline_v2/evidence/rejection-table.md`; `examples/image_pipeline_v2/evidence/demo-run-excerpt.txt`; `examples/image_pipeline/nodes/generate_images.py`; cited target repo `sheikkinen/deviant-daily@5bd0bab`: `training/generate.py`, `training/evidence/rejection-stats.md`. `feature-requests/FR-879-image-pipeline-v2-critic-filter.judgement.md` was cited by FR-881 but is not present in this repo.

## What is sound

The first consumer and first event are concrete: the operator wants one run that samples 10 prompts from the FR-876 trained local model, filters them locally, and renders only survivors (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:10-16`). That is a real demonstration event, not speculative framework growth.

The strategic classification is **Contrib/example**. **Prior art:** dispositioned in the FR (FR-879 dependency, FR-876 consumed, FR-109/FR-202/034/020 no overlap) and verified here. The proposal adds a sibling example that demonstrates an already-built external model as a graph input source; it does not claim a new YAMLGraph primitive. That fits the repo's three-layer doctrine: yamlgraph orchestrates, deviant-daily owns the model and corpus, and Replicate remains the render side effect (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:62-80`).

The dependency on FR-876 is evidenced. FR-876 records the trained model as enforced, including the 3,299,328-param run, final validation loss 1.0175, and the t0.8 pass-rate table (`feature-requests/FR-876-minimal-llm-training-demo.md:228-269`). The cited rejection statistics support the FR-881 default: transformer t0.8 passed 165/200 samples with only 2 novelty and 33 shape rejections (`sheikkinen/deviant-daily@5bd0bab:training/evidence/rejection-stats.md:1-8`).

The v2 chassis is real and suitable precedent. FR-879 is marked enforced and records the delivered score/filter/render graph, authoring route, and witnessed run (`feature-requests/FR-879-image-pipeline-v2-critic-filter.md:178-204`). The current v2 graph already imports the v1 `generate_images_node` and sequences `generate_candidates -> score_filter -> save_report -> generate_images` (`examples/image_pipeline_v2/graph.yaml:28-82`). The v2 evidence shows the expected committable pattern: sanitized rejection table plus run excerpt, with image paths logged rather than generated binaries committed (`examples/image_pipeline_v2/evidence/rejection-table.md:1-34`; `examples/image_pipeline_v2/evidence/demo-run-excerpt.txt:1-20`).

The no-LLM-generator lesson is crisp. FR-881 explicitly forbids an `llm` node and an LLM fallback (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:89-97`), which preserves the demo's headline and aligns with the repo's "plausible wrong answer" doctrine.

## Required revisions

### R-1: Correct the FR-879 dependency and evidence references

Revise FR-881 so it reflects the actual state of its dependency. The FR says FR-879 is "in flight" and enforcement should wait for it to merge (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:8-9`, `175-176`), but FR-879 itself records `Status: Enforced` and implementation details (`feature-requests/FR-879-image-pipeline-v2-critic-filter.md:178-204`). FR-881 also cites an FR-879 judgement (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:165-166`) that is not present in the repo.

Fold this mechanically by changing the dependency line to the committed FR-879 artifact actually available, removing the nonexistent judgement citation, and stating that enforcement must use the delivered v2 graph/nodes/evidence as the chassis. If a later FR-879 judgement is added before enforcement, cite that concrete file; otherwise do not claim it exists.

### R-2: Freeze "first k passers" everywhere and delete ranking alternatives from the executable plan

The Decisions section correctly resolves ranking to "first k passers" (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:170-174`), but the Proposed Solution still authorizes "fewest attempts" or possible FR-879 NLL ranking at enforce time (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:98-101`). That leaves the enforcer with two incompatible implementation paths.

Fold this by rewriting the Proposed Solution and acceptance criteria so v3 preserves sampling order and renders the first `top_k` boundary-passing prompts. Do not call `training/score.py`, do not calculate NLL, and do not rank by attempts. Attempt counts may appear in the report only as generation diagnostics, not as selection criteria.

### R-3: Specify an exact `training/generate.py --json` contract

The current deviant-daily generator has `--n`, `--temp`, `--top-k`, `--cond`, `--start`, `--seed`, and `--out`, but no `--json`; it prints human markdown-ish blocks for accepted samples and rejection reason lines for failed attempts (`sheikkinen/deviant-daily@5bd0bab:training/generate.py:29-90`). FR-881's proposed JSON object (`prompt, attempts, verdict_counts, seed, temp, cond, start, ckpt_sha`) is under-specified for the promised rejection table and does not say whether output is one record per accepted prompt, one summary row, or mixed event rows (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:70-77`).

Fold this by defining the JSONL shape exactly. Required minimum: stdout in `--json` mode contains only JSON lines; one `candidate` object per accepted prompt in generation order with `ordinal`, `prompt`, `attempts_for_candidate`, `verdict_counts`, `seed`, `temp`, `top_k`, `cond`, `start`, `ckpt_sha`, `corpus_sha`, and `git_sha`; one final `summary` object with total attempts and aggregate verdict counts. Rejected raw text must never appear in stdout, stderr, JSON, reports, or committed evidence; only rejection reason counts may be persisted. Add tests for parseable JSONL, provenance stamping, deterministic seed behavior, and absence of rejected raw text.

### R-4: Resolve `save_report` reuse without writing v3 output under the v2 directory

FR-881 says `save_report` should reuse the v2 node and that v1/v2 diffs stay empty (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:82-86`, `102`, `127-128`). The current v2 `save_report_node` hardcodes `outputs/image_pipeline_v2` (`examples/image_pipeline_v2/nodes/save_report.py:9`, `29-63`). Importing it as-is from v3 would produce v3 run artifacts in the v2 output tree, while copying it would violate the FR's reuse rule.

Fold this by adding a v3 report node that writes to `outputs/image_pipeline_v3` while importing reusable table constants/helpers from v2, or by extracting a tiny shared report helper without changing v2 behavior. The revised FR must name the chosen surface and require a regression check that v2 still writes to `outputs/image_pipeline_v2`.

### R-5: Replace committed rendered images with sanitized demo evidence

AC-05 currently requires "rejection table + k rendered images" to be committed (`feature-requests/FR-881-image-pipeline-v3-local-model-generator.md:124-126`). That is heavier than the precedent FR-879 actually used: sanitized rejection table and run excerpt were committed, while rendered image paths were logged (`examples/image_pipeline_v2/evidence/rejection-table.md:1-34`; `examples/image_pipeline_v2/evidence/demo-run-excerpt.txt:6-20`). Committing generated binaries is not necessary to prove the graph path, increases repo weight, and risks carrying full prompt text through sidecars or metadata.

Fold this by requiring committed evidence to include a sanitized rejection/generation table, a demo output excerpt, image paths or checksums for the `top_k` renders, and per-sample read notes. Generated PNGs and any local full-prompt sidecars stay out of git unless a separate human decision explicitly authorizes binary evidence.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-881-image-pipeline-v3-local-model-generator.md` folding R-1 through R-5 |
| D-2 | Sibling repo `sheikkinen/deviant-daily`: extend `training/generate.py` with the frozen `--json` contract and tests |
| D-3 | `examples/image_pipeline_v3/graph.yaml`, README, and any required `examples/image_pipeline_v3/nodes/*.py` / `prompts/*.yaml`, authored through the graph-authoring route |
| D-4 | Reuse existing `examples/image_pipeline/nodes/generate_images.py` for rendering; reuse v2 report/table code only in a way that preserves v2 output behavior |
| D-5 | Sanitized committed evidence under `examples/image_pipeline_v3/evidence/` and implementation-status notes in FR-881 |

Not authorized: yamlgraph core/runtime changes; new LLM provider support; an `llm` node in v3; LLM fallback generation; use of `training/score.py` or NLL ranking; changes to deviant-daily training/model architecture, boundary policy, corpus extraction, publisher, or `draw_prompt()`; vendoring or submoduling deviant-daily into yamlgraph; modifying v1 behavior; changing v2 semantics or output paths; committing generated PNGs, local full-prompt sidecars, raw rejected samples, secrets, or model checkpoints; invoking another judge route.

## Revised acceptance criteria

- [ ] AC-01: FR-881 is revised before enforcement to fold R-1 through R-5 and to cite only committed, present artifacts.
- [ ] AC-02: `training/generate.py --json --n 10 --temp 0.8 --cond prose --start "<seed>" --seed <n>` emits parseable JSONL on stdout with exactly 10 `candidate` records plus one `summary` record, using the schema frozen in R-3.
- [ ] AC-03: deviant-daily tests prove JSONL shape, provenance fields, deterministic seed output for a fixture model or sampler seam, and rejected raw text never appearing in stdout, stderr, JSONL, or report artifacts.
- [ ] AC-04: `examples/image_pipeline_v3/graph.yaml` is authored via `scripts/author.sh` with `tmp/draft-authoring-report.md` evidence, lints cleanly, and contains no node with `type: llm`.
- [ ] AC-05: `sample_candidates` uses `DEVIANT_DAILY_DIR` and the sibling repo virtualenv to call `training/generate.py --json`; missing clone, venv, checkpoint, corpus, or malformed JSON fails fast with actionable setup/train commands and no LLM fallback.
- [ ] AC-06: Selection is exactly the first `top_k` boundary-passing candidates in generator order; no NLL, scorer, fewest-attempts, or LLM-judge ranking is used.
- [ ] AC-07: The v3 report records all accepted candidates, selected status, per-candidate attempts, aggregate rejection reason counts, sampling params, and provenance SHAs; it contains no raw rejected prompt text.
- [ ] AC-08: `generate_images` renders only the selected `top_k` prompts via Replicate z-image using the existing v1 render node import path, with sidecar/EXIF behavior unchanged.
- [ ] AC-09: Committed demo evidence includes a sanitized generation/rejection table, demo output excerpt, image paths or checksums for rendered survivors, and per-sample read notes; generated PNGs and local full-prompt sidecars are not committed.
- [ ] AC-10: v1 behavior is untouched, and v2 still writes reports under `outputs/image_pipeline_v2`; if v2 code is refactored to share a helper, a targeted regression check proves the v2 output path and sanitized table shape remain unchanged.
- [ ] AC-11: README documents cross-repo setup, the no-LLM-until-render cost/privacy boundary, required environment variables (`DEVIANT_DAILY_DIR`, Replicate credentials for rendering), graph variables, output artifacts, and known local-model limits.
- [ ] AC-12: The implemented v3 graph has lint and smoke evidence from a `--start`-seeded run with `n_candidates=10` and `top_k=3`; if Replicate credentials are unavailable, enforcement stops rather than substituting mocked images for the demo evidence.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into FR-881. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Any creation or material modification of `examples/image_pipeline_v3/graph.yaml` or `prompts/*.yaml` must go through the graph-authoring sole route and be evidenced by `tmp/draft-authoring-report.md`. | GATE |
| C-4 | No `llm` node, LLM fallback, scorer/NLL ranking, or fewest-attempts ranking may enter v3. | GATE |
| C-5 | The sibling repo boundary is hard: call deviant-daily through `DEVIANT_DAILY_DIR`; do not vendor, submodule, archive, or commit that repo into yamlgraph. | GATE |
| C-6 | Raw rejected generated text, generated PNGs, full-prompt local sidecars, secrets, and model checkpoints must not be committed as evidence. | GATE |
| C-7 | If implementation requires changing deviant-daily model training, corpus extraction, publication flow, `draw_prompt()`, yamlgraph core runtime, or v1/v2 behavior beyond an explicitly behavior-preserving report-helper extraction, stop for a separate FR. | GATE |

Authority granted: after the required revisions are folded, enforcement may add the minimal deviant-daily JSON generation contract and the yamlgraph `examples/image_pipeline_v3` local-generator demo that samples boundary-passing prompts offline, records sanitized attempt/provenance evidence, and renders only the first `top_k` survivors via the existing z-image path.
