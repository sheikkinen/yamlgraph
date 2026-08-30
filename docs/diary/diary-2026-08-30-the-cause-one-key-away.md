# The Cause One Key Away

**Date:** 2026-08-30
**FR:** FR-926 — research route failure must cite the recorded cause

## What happened

Three research runs failed with `missing persona findings:
yamlgraph_native_finding`. Recovering the real cause — a
`string_too_long` validation rejection on `rationale`, retried and
re-failed identically — took a throwaway LangSmith script walking 47
child runs. The information was never absent. `state["errors"]` held a
fully structured `PipelineError` at the exact moment `gather_findings`
raised, and the raise read the missing-keys list only.

## The trap

`read_raw_output_first` has a mirror image I had not named:
**write_raw_cause_first**. The Scripture warns against building rulers
to explain a bad number when the artifact is sitting in plain text.
This was the producing end of the same failure — the code had the
artifact in hand and emitted the number.

The generalized shape: *a failure record that exists but is never
surfaced is equivalent to no record at the moment of diagnosis.* The
error channel satisfied every presence check CAP-08 defines. It was
populated, typed, and correct. It just never reached a human. That is
`gate_checks_shape_not_substance` applied to observability: the system
passed "errors are recorded" while failing "errors are legible".

## What the judge added that I would have missed

The FR's own illustrative code filtered with `isinstance(e, dict)`.
The retry handler stores `PipelineError.from_exception(...)` — Pydantic
objects. The proposed fix would have silently rendered nothing for the
exact error class that motivated the FR: a visibility fix invisible to
its own witness. The judge caught it by reading `error_handlers.py`
rather than the FR's prose. `judge_as_junior_pr` earning its keep —
plausible code hiding a subtle bug, in an FR whose entire subject was
things that look present but are not.

The cure in code avoids the coupling entirely: duck-type on
`model_dump`, so a demo module never imports framework schemas to
recognize a framework object.

## The provenance snag

R-3 asked me to repair a dangling brief citation appearing in both the
FR header and the promoted research record. Editing the record would
have broken it: `research_preflight.py --verify-promotion` pins
`FR-926.research.md` by sha256 against `research-runs.jsonl`. The
correct move was to fix only the mutable half (the FR header) and
document why the immutable half keeps its label. Provenance stamps make
some artifacts read-only after the fact — a revision instruction that
targets one is asking for a forgery, not a correction.

## Heuristic

**Every raise adjacent to a populated error channel must read it.**
When a node fails on missing state, the reason that state is missing is
usually one key away, already structured. Surfacing costs a formatter;
not surfacing costs a tracing-backend investigation per incident.

## Seed

The retry handler recorded the failure, the graph raised on the
consequence, and the two never met. How many other boundaries in this
repo hold a structured cause at raise time and emit only the symptom —
and could a lint rule find them by looking for raises inside functions
whose state contract includes `errors`?
