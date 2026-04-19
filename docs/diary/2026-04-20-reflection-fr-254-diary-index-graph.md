# Reflection: FR-254 Diary Index Graph — Framework Indexes Its Own Reflections

**Date:** 2026-04-20
**FR:** FR-254
**Branch:** feat/fr-254-diary-index-graph

## What Was Done

Built `examples/demos/diary-index/` — a YAMLGraph demo that reads all diary entries from `docs/diary/*.md`, fans out via a `type: map` node, extracts structured data (traps, heuristics, seeds, FR references) from each entry using `type: llm` with an inline schema, then aggregates into a cross-reference index (`docs/diary-index.yaml`) via a deterministic Python `aggregate_index()` node. Model: `claude-haiku-4-5` for cost control.

## Cognitive Trap: The Corpus Is the Tool

The interesting structural moment here is that the framework is being used to analyze its own diary — the reflection mechanism is now recursive. The diary was created to teach the framework's authors; the index graph now uses the framework to extract structured knowledge from those same entries. This is a form of **demo_vs_test** insight: the demo doesn't just prove the `map` node abstraction works, it proves that the abstraction is worth having by doing something non-trivial with it.

The trap to watch: recursive self-analysis can produce plausible wrong answers. The LLM extracting "heuristics" from diary entries may surface syntactically correct but semantically shallow patterns. The `2+ threshold` on `heuristics_candidates` (must appear in ≥2 entries) is the first guard; human review before Scripture graduation is the second.

## Heuristic

**Demos prove abstractions, not just correctness**: A demo that uses a framework feature to solve a real problem the team actually has (knowledge discovery in a 450+ entry corpus) is worth 10 unit tests at demonstrating the abstraction's value. Budget one demo per major node type; make it solve a real problem.

## Seed

The diary index is static — run on demand. Could the index graph run automatically on each PR merge (as a CI step), updating `docs/diary-index.yaml` and committing it? That would give the Scripture graduation process a live feed of graduating heuristics without any manual grep. The cost is ~N × Haiku calls per PR (one per new diary entry), which is negligible.
