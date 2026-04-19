# Reflection: FR-249 Guardrails Pattern Documentation

**Date:** 2026-04-19
**FR:** FR-249
**Type:** Documentation pattern

## Cognitive Process

The guardrails pattern (echo → validate → respond) was already implemented in
`examples/openai_proxy/` but was invisible in the patterns reference. This is the
classic **documentation-as-discovery** gap: a capability exists but new users
can't find it because it's buried in example code.

## Trap Encountered: working_system_inertia

The openai_proxy example was "working" and well-tested, which created the illusion
that the guardrails concept was documented. But `reference/patterns.md` — the
canonical location where graph authors discover reusable patterns — had no mention
of it. The Knowledge Graph calls this `working_system_inertia`: "'It works' blocks
seeing it clearly."

## Insight

Pattern 11 fills the gap between Pattern 10 (Batched Map Processing) and Pattern 12
(Quality Gate for Map Output). The numbering gap was itself a signal — Pattern 11
was always waiting for the input-side validation pattern to complement Pattern 12's
output-side validation. Input guardrails + output quality gates = complete pipeline
safety.

## Heuristic

When an example demonstrates a production-critical safety pattern, the pattern
reference is the minimum viable documentation — not the example README alone.
Examples show *how*; patterns explain *when* and *why*.

## Seed

Could YAMLGraph offer a `guardrails` graph template via `yamlgraph init --template guardrails`
that scaffolds the echo → validate → respond pipeline with stub tools, similar to
how web frameworks scaffold auth middleware?
