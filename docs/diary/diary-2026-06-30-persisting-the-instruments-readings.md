# Persisting the instrument's readings

**Date:** 2026-06-30
**Arc:** plot_modeller round-trip skeleton — FR-623 (persist run artifacts), judged then enforced
**FRs:** FR-623 (implemented); follows FR-613 K=6 read, FR-622 re-scope

## What happened

The prior finding (FR-613) was that the skeleton is an *instrument* whose value is the
readings it produces, not the book. But the instrument recorded **nothing** — every run's
`cast`/`briefs`/`book`/`coherence` was computed into state and discarded at process exit.
The K=6 read only happened because I hand-redirected `--full` stdout into `logs/p3-raw/*.log`,
and `briefs` — the richest artifact — truncated in the console. FR-623 adds a deterministic
`persist_run` leaf at the tail of the spine that writes each stage to a run-stamped directory.

Judged it as a junior PR before building. The Judge caught three real defects in my own
proposal, the sharpest being the manifest's `model` field.

## The trap

**`state_as_provenance`.** I wrote the manifest to record `{premise, genre, model, ...}` and
specified `persist_run` would read them "from state." But `model` and `provider` are **not in
graph state** — they enter at the **run boundary** as `PROVIDER` / `ANTHROPIC_MODEL` env vars
and never touch a state key. The tool *could not* have read `model` from state; the field was
unfulfillable as written, and a naive implementation would have silently written `null` or
crashed on a missing key. The provenance of a run lives at the boundary where the run was
launched, not in the dataflow the run produced.

This is the same boundary law that runs through the whole diary, seen from a new side:
normalize/source data at the boundary where it enters. Model identity enters at the
environment boundary; the manifest must reach *there* for it, not into state. I had reflexively
assumed "it's run metadata, so it's in the run's state" — conflating two different boundaries
(the env/CLI launch boundary vs. the graph-state dataflow boundary).

The other two folds were the same family of "shape passes, substance fails": an undeclared
`artifacts` state_key (the dynamic builder would not allocate it) and a second-granularity
`run_id` that collides on rapid rerun — which would have *clobbered* the very two-draw case
(Loom 0.40 vs 0.00) the run stamp exists to separate.

## The heuristic

> Provenance is sourced at the launch boundary (env/CLI/clock), not read from the artifact's
> own state. When a manifest wants to record *how* a run was produced — model, provider,
> timestamp, seed — reach for the environment and the clock, never for a state key the run
> never wrote. A "metadata" field that names the producer is a boundary read, not a dataflow
> read.

Corollary, reaffirmed: judge the proposal before building it. Three of three corrections here
were invisible in the prose of the FR and obvious the moment I asked "where does this value
actually come from?" The cheapest bug is still the one killed in the spec.

## Seed

`persist_run` is a per-graph leaf reimplementing run-stamping, manifest provenance, and
env-sourced model capture that *every* graph would want. Should provenance capture be a
framework primitive — a `run_manifest` the executor writes for any graph (run_id, env-sourced
provider/model, node timings, trace URL) — so individual graphs persist only their *domain*
artifacts and never re-derive the boundary metadata? **Seed:** what is the minimal provenance
record the runtime could emit for free, and would making it a primitive finally let the
"instrument records its own readings" property hold by default instead of per-FR?
