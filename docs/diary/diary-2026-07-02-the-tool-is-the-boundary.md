# Diary: 2026-07-02 — The Tool Is the Boundary

## Context
FR-657: Agentic event deepening with canon lookup tools for worldgen.

## The Trap: Gate Checks Shape Not Substance

The initial instinct for fixing worldgen quality was Option A — dump all canon YAML into the deepen prompt context. 13K tokens, throw it at the LLM, hope it reads the right parts. This is the **omnipotent LLM** trap: the belief that more context equals more reliability.

The operator's correction was surgical: "Option A reeks of omnipotent LLM thinking. Tools would give in-progress validation possibility." Five words that restructured the entire architecture.

## The Insight: Tools Create Enforcement Boundaries

A context dump has zero enforcement boundaries. The LLM can receive Ulf's full page and still name Hilde's father "Ottokar" — there is no mechanism to catch the error mid-generation.

A tool has one enforcement boundary per call:
- `lookup_canon_page("ulf")` → response injects "Calendar convention: Year 0 = the Great Flood"
- `validate_draft(yaml)` → returns `{"valid": false, "errors": ["year 28 is positive"]}`

The LangSmith trace becomes the audit trail. If the agent never called `lookup_canon_page("ulf")`, the name collision is traceable to a missing lookup — not a missed detail in a 13K token wall.

## The Pre-Commit Gauntlet

The enforcement commit traversed 6 hook failures before landing:
1. `ruff-format` — reformatted 2 files
2. `req_coverage --strict` — phantom REQ-YG-509 (needed CAP-182)
3. `cap-architecture-sync` — auto-generated ARCHITECTURE.md
4. `noqa-confession` — undocumented `# noqa: ANN202` (needed CONF-348)
5. Plus the copilot test mock target fix (subprocess moved to copilot_runtime)

Each gate caught a real gap. The "pre-existing failure" reflex — blaming the copilot test on someone else's refactor — was wrong. The subprocess import moved; the mock target didn't follow. Current change author owns the red suite.

## Heuristic

**tool_boundary_over_context_dump**: When an LLM needs to cross-reference external data, give it tools with enforcement at each call — not a context dump and hope. Each tool response is a checkpoint where constraints are injected and compliance can be validated. The trace log makes errors traceable to missing lookups, not missed context.

This is Scripture's `the_one_law` applied: "Normalize at the boundary where external data enters." The tool response IS the boundary.

## Seed

The agent currently re-loads all 30 canon YAML files on every tool call (`_load_canon()` called per lookup). With 12 events × 3-5 lookups each, that's 36-60 full directory scans per worldgen run. Should the tools cache the canon in a closure, or is the I/O cost negligible compared to the LLM latency? At what canon size does the cache matter?
