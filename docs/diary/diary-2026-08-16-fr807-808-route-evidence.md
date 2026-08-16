# Diary: FR-807/808 Route Evidence Boundary

**Date:** 2026-08-16
**FRs:** FR-807, FR-808

## What happened

The route logger already emitted useful decisions, but the record could not
prove which graph and prompts produced them. Its exception suppression also
made evidence loss indistinguishable from zero routes. FR-807 added one
content-bound run envelope, timestamps, shared run identity, overlay validation,
and a counted non-strict loss channel. FR-808 then added the policy layer:
artifact-declared regulated runs require a per-run sink and judgement reference,
and strict runs fail when that channel loses evidence.

## Reflection

The trap was **observability mistaken for evidence**. A log line can describe an
event while remaining unbound to the artifact, run, time, and delivery outcome.
Adding more fields downstream would not repair that; identity and loss semantics
had to be owned by the run boundary.

A second boundary detail mattered: `PipelineError` is structured graph state,
not an exception class. The judged phrase "raises a PipelineError" could not be
implemented literally. `EvidenceLossError` therefore carries the structured
record rather than changing a widely used state model under this FR.

**Heuristic:** An audit record is trustworthy only when it identifies its
source artifact, scopes one run, timestamps its events, and accounts for its own
delivery failures.

**Seed:** Should every retained output artifact share the same canonical
artifact manifest and run identity, so route logs, exports, and evaluation
results can be joined without adapter-specific provenance code?
