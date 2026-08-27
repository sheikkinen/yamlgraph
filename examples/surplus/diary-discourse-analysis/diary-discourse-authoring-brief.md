# Diary Discourse Corpus Reader

## Purpose

Create a disposable YAMLGraph research instrument that reads the complete
committed diary corpus and produces an evidence dossier for a human-authored
philosophical thesis and Socratic discourses. The graph must not write the
thesis, propose feature requests, extract implementation tasks, or modify any
tracked repository artifact.

The target directory is `tmp/diary-discourse-analysis/`. Create:

- `tmp/diary-discourse-analysis/graph.yaml`
- `tmp/diary-discourse-analysis/prompts/read_chunk.yaml`
- `tmp/diary-discourse-analysis/prompts/distill_batch.yaml`
- `tmp/diary-discourse-analysis/nodes/tools.py`
- `tmp/diary-discourse-analysis/fixtures/` with a tiny representative corpus
- `tmp/diary-discourse-analysis/README.md`

Write live output only to `tmp/diary-discourse-analysis/dossier.json` and a
compact `tmp/diary-discourse-analysis/dossier.md` index.

## Existing Inputs

- The existing `docs/diary/` directory is the main diary corpus.
- The existing `docs/diary-2026-02-17.md` demonstrates the legacy root-level
  diary files; collect all root-level `docs/diary-*.md` files as well.
- The existing `docs/FR-884-session-task-shapes.md` is a behavioral control
  report derived from session traces.
- The existing `docs/FR-884-raw-read-log.md` records the privacy-safe raw-read
  observations behind that report.
- The existing `examples/demos/prompt_theme_analyzer/graph.yaml` is the primary
  architecture precedent: ingress normalization, map classification,
  deterministic assembly, semantic grouping, deterministic write.
- The existing `examples/demos/session-shapes/graph.yaml` is the privacy and
  pinned-cheap-model precedent.
- The existing `examples/demos/fr-atlas/graph.yaml` is the chunked-corpus and
  mechanical coverage-reconciliation precedent.

## Required Shape

Use YAMLGraph itself for a two-level map/reduce reading:

1. A Python ingress tool collects all `docs/diary/*.md` and root-level
   `docs/diary-*.md` files, normalizes UTF-8 text, records path and SHA-256,
   and reports empty files rather than silently substituting or dropping them.
2. Deterministically chunk the corpus at a target of 60,000 characters. Keep
   source-path and span metadata in every chunk. Split oversized files only at
   paragraph or heading boundaries when possible.
3. Map one Mercury-2 structured reading over every chunk. Each reading has one
   job: render an interpretive memorandum about what the evidence teaches.
   Supporting fields may name the central tension, durable lesson, correction
   or contradiction, unresolved question, and up to three short path-cited
   evidence excerpts. It must not turn observations into software tasks.
4. Deterministically batch the memoranda in groups of at most eight.
5. Map one Mercury-2 structured distillation over each batch. Each distillation
   identifies teachings that survive disagreement, important contradictions,
   and questions suitable for Socratic examination. Preserve source paths.
6. A Python writer emits the full raw memoranda, batch distillations, corpus
   manifest, coverage reconciliation, and run budget into JSON. The markdown
   output is only a navigable index, not the final essay.

The graph defaults must pin `provider: inception`, `model: mercury-2`, and a
low temperature suitable for structured analysis.

## Cost And Coverage Bounds

The measured input on 2026-08-26 is 1,279 files, 4,609,375 bytes, and roughly
1.15M input tokens. Set a hard maximum of 96 primary chunks and 12 reduction
batches. Fail loudly if the corpus exceeds either bound. A normal full run
should make about 87 LLM calls and can never exceed 108 calls.

Coverage is a mechanical invariant. The dossier must prove:

- every collected non-empty source byte belongs to exactly one chunk span;
- every primary chunk has exactly one memorandum;
- every memorandum belongs to exactly one reduction batch;
- no map error is silently skipped;
- input and output counts are shown explicitly.

Do not include the FR-884 control documents in the diary map. Package their
paths and full text separately in the dossier so the requesting session can
compare behavioral traces against diary self-report after the independent
diary reading.

## Prompt Constraints

Treat diary prose as a fallible first-person record, not doctrine and not a
backlog. Look for changes of mind, repeated failures under new names,
differences between claimed values and observed behavior, insights that travel
beyond software, and questions whose uncertainty should be preserved.

Do not use frequency as a proxy for truth. Do not force every observation into
the existing trap vocabulary or the One Law. Do not summarize file-by-file.
Do not praise the project. Evidence excerpts must be short and carry exact
workspace-relative source paths.

## Validation

Run:

```bash
yamlgraph graph lint tmp/diary-discourse-analysis/graph.yaml
yamlgraph graph run tmp/diary-discourse-analysis/graph.yaml --var corpus_dir=tmp/diary-discourse-analysis/fixtures --var include_legacy=false --var output_dir=tmp/diary-discourse-analysis/smoke --full
```

The smoke must use the live pinned Mercury-2 provider if credentials are
available. Verify the JSON coverage fields and that the markdown index exists.
Record exact outcomes, repairs, and any blocked validation in
`tmp/draft-authoring-report.md` using the required report headings.
