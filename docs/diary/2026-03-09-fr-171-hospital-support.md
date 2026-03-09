# Diary: FR-171 — Hospital Support Line Outcaller

**Date:** 2026-03-09
**FR:** OC-009 (origin: FR-171)
**Type:** Feature — deterministic telephony smoke test

## What Happened

Built a fully deterministic Finnish hospital support line outcaller demo. Linear graph: 4 passthrough nodes emit fixed Finnish phrases, tool nodes handle Twilio/ElevenLabs telephony. Zero LLM calls. One-line `stt.py` fix enables Finnish STT via `stt_language` state key.

## Trap: Mock Machinery as False Witness

Initial plan included full async ElevenLabs mock tests for the `state.get("stt_language", "en")` one-liner. The mock scaffolding (async event loops, mock sessions, mock SDK clients, capture dictionaries) was an order of magnitude more complex than the code under test. The mock was testing itself, not the production path.

**The tell:** when the mock session's `is_disconnected=True` caused early return before reaching the connect call, the instinct was to add *more* mock complexity to work around the mock's own behavior. That's the signal: you're debugging the test harness, not validating the feature.

**Cure:** Strip the mock tests entirely. The real proof is calling a Finnish number and hearing Finnish STT work. Graph structure tests (YAML shape, UTF-8 strings, no LLM nodes, edge topology) are cheap, fast, and directly witness the contract. The `state.get()` line gets its proof from the live demo — that's what a smoke test *is*.

## Heuristic: Demo Tests ≠ Unit Tests

When the deliverable IS the smoke test, the appropriate witness is the smoke test itself. Unit-testing the internal wiring of a telephony tool node with mocked async SDK calls adds cost without adding confidence. Structure tests witness the contract (correct strings, correct edges, correct node types); the live run witnesses the integration.

**Graduated from:** `demo_vs_test` in the Knowledge Graph — "Tests prove constraints; demos prove abstraction worth having."

## Insight: Passthrough as Structural Guarantee

Using `type: passthrough` for all content nodes means the graph *structurally cannot* make LLM calls. The `test_no_llm_nodes` test witnesses this at the YAML level — no runtime assertion needed. The type system (node type → factory function) makes the guarantee: passthrough nodes call `resolve_template()` on literal strings, which returns them unchanged. The guarantee is architectural, not behavioral.

## Seed

Can passthrough-only graphs serve as a general regression pattern for multi-language telephony stacks? A matrix of `{language: X, phrases: [...]}` graphs would test STT/TTS/Twilio for each locale without LLM variance. The passthrough node is the ideal vehicle: deterministic input, deterministic routing, stack failures isolated from LLM failures. What would a `graph-matrix` CLI command look like that generates locale-specific graphs from a template?
