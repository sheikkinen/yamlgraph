# Reflection: FR-273 Watcher2 Phase 3 — Planning Pipeline

**Date:** 2026-04-22
**FR:** FR-273 (Phase 3)

## Trap: Session ID Absence

The copilot CLI does not emit session IDs when run with `--silent` and `capture_output=True`.
The `SESSION_ID_PATTERN` regex (`Session: <id>`) matches nothing in stderr. This means
`--resume` flags in steps 2-4 resolve to `None` and each step starts a fresh session.

This is acceptable because each step reads the FR draft from disk, not from session memory.
The session chain is a performance optimization (shared context), not a correctness requirement.

**Heuristic:** When designing multi-step copilot chains, ensure each step can operate
standalone by reading artifacts from the filesystem. Session resume is a bonus, not a contract.

## Insight: Step Graphs as Composition Units

Creating separate single-node graphs (`step-plan.yaml`, `step-research.yaml`, etc.) that
reuse existing prompts via `prompts_dir: ../copilot/prompts` is the right granularity for
shell orchestration. Each graph is a unit that the orchestrator can invoke, skip, or retry
independently.

The alternative — `--start-node`/`--stop-after` flags — would have been more elegant but
requires framework changes. The step graph approach is zero-framework-change and works today.

## Insight: Verdict Parsing

The judge verdict is extracted from `CopilotResult.output` using simple string matching
(`APPROVE`, `REJECT`, `AMEND`, `SPLIT`). This is fragile — the copilot could phrase it
differently. The `tolerant_matching` cure from Scripture applies: use contains/prefix,
not exact equality for LLM outputs.

**Seed:** Should verdict extraction use a structured output schema instead of regex on
freeform copilot output? A Pydantic `Verdict` model could enforce the contract at the boundary.
