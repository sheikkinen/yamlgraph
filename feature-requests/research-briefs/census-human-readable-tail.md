# Problem brief: the census pipeline has no stage whose reader is a human

**Prior art:** dispositioned in the FR this brief produces (closed-input
brief per FR-890 R-2).

## Problem statement

The corpus-census pipeline (merged, two proof corpora, one full-corpus
production run of 1266 items) emits machine-consumer artifacts at every
stage: an 8-column evidence ledger (markdown + JSONL) consumed by
aggregators, and an aggregated recurrence table consumed by graduation
tooling. When the operator opened a proof ledger and asked "is there a
human readable summary?", the answer was no: no shipped stage of the
pipeline has the human as its reader. The plan lineage carried a
human-facing synthesis output through two artifacts and lost it at the
third — the feature-request marked it "optional", and the implementation
brief cut it citing scope discipline. Consequence: every census run ends
in a table that answers "what was judged, with what evidence" while the
question the run was commissioned for — "what does this corpus say?" —
is answered by nobody, or hand-written after the fact. The 1266-entry
diary census's findings narrative currently exists only as prose written
manually into the feature request's implementation record; nothing
regenerates it when the census re-runs.

## Classification

judgement/analysis/generation

## Constraints

- The census pipeline's existing contract is frozen by prior judgement:
  fail-closed LLM-free reducer, 8-column ledger (markdown + JSONL),
  invocation-time tool slots; changes to graph or prompt artifacts are
  governed by the sole authoring route with recorded lint/smoke evidence.
- Cheap-map discipline: model tier follows per-call abstraction-span;
  a single synthesis over an aggregated artifact is one call and may be
  a stronger model than the map tier; expensive models never in fan-out.
- Any human-facing narrative must cite the ledger rows it draws from
  (evidence discipline; a narrative without citations is a
  plausible-wrong-answer surface) and must not contradict the ledger.
- Public repo: committed narratives inherit the census's public-safe
  contract (the diary census commits no raw evidence spans).
- Prior judgements' C-6 discipline: no generic template/override
  mechanisms; the smallest sufficient change to the existing pipeline.
- Witnessed run scales: 3-row proof ledgers to 1700-label aggregations;
  the human artifact must be useful at both ends.

## Witnessed incidents

- 2026-08-27: operator opened
  examples/demos/corpus_census/proofs/pdf-library/ledger.md and asked for
  a human-readable summary; none exists by construction.
- 2026-08-26: the diary census (1266 entries) produced its headline
  finding — top recurrences are aliases of graduated doctrine — only
  because a session author happened to read the table and write prose
  into the FR record; the insight is not reproducible by re-running.
- Plan lineage of the loss (diary
  2026-08-27-optional-is-where-value-goes-to-die.md): study artifact
  named the executive-brief output; the feature request demoted it to
  "optional"; the authoring brief deleted it as scope creep. Three
  artifacts, one value, silently gone — "optional" marked the only
  human-reader stage.
