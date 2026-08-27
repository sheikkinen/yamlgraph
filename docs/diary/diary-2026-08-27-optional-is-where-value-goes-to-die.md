# Diary — "Optional" Is Where Value Goes to Die

**Date:** 2026-08-27
**Context:** Operator, reading the PDF-census ledger: "is there a human
readable summary?" There isn't. Tracing where it went: the mercury study's
run-1 matrix named the executive brief (cheap calls gather facts, ONE
synthesis call writes the narrative) as a ⭐5 cell; FR-892's Proposed
Solution carried it as "optional tail synthesis node"; my authoring brief
executed it as "Optional `synthesize` tail: SKIPPED in v1 (out of scope
creep)". Three artifacts, one value, silently gone.

## The trap: value_marked_optional

The word "optional" in a plan is not a priority label — it is a death
sentence with delayed execution. Every mandatory stage of the census
pipeline serves a MACHINE consumer (ledger → aggregator, JSONL → tools);
the one stage serving the HUMAN consumer was the one marked optional, so
it was the one that died at the first scope pressure. The FR carried the
value; the enforcement layer (my brief) discarded it, correctly citing
anti-scope-creep doctrine — the doctrine's own purge instinct ate the
consumer-facing half of the product. `who_reads_this_when` failed at the
stage level: I asked it of the artifacts, never of each pipeline stage.
Had I asked "who reads the ledger?" the answer — aggregators and
auditors, not the operator — would have exposed that NO shipped stage
had the human as its reader.

## The sharper form

When a plan splits into mandatory-for-machines and optional-for-humans,
the split itself is the defect: the human-facing output is not a garnish
on the machine artifact, it is the other half of the deliverable. Scope
cuts should trim BREADTH (fewer corpora, smaller runs), not delete a
CONSUMER CLASS. Cutting the only human-reader stage is not a smaller
product; it is a different product.

## Cure applied

FR-895 filed same day (research-route lifecycle): optional-no-more —
the synthesize tail as a first-class stage with the diary census as
first consumer.

## Seed

**Seed:** Should the Judge's rubric ask, for every pipeline FR, "which
stage does the HUMAN read, and is it mandatory?" — a consumer-class
completeness check, the `who_reads_this_when` question applied per-stage
at judgement time, before "optional" can be written at all?
