# FR-178: Moving the LLM Call from Python to YAML

**Date:** 2026-03-10
**Feature:** FR-178 — Eliminate `execute_prompt()` from probe_recap Python tool node

## What happened

The `extract_answers()` function in `probe_recap.py` called `execute_prompt()` directly from a Python tool node. This violated the three-layer architecture: LLM calls belong in YAML graphs, not Python tools.

The fix was straightforward:
1. Convert `extract_answers` from `type: python` to `type: llm` in both `outcaller.yaml` and `incaller/graph.yaml`
2. Replace the Python function with `merge_extraction()` — a pure state-merge function that reads `extraction_result` from state (written by the llm node) and merges non-null values

## Cognitive traps encountered

**working_system_inertia**: The code worked, so the structural defect was tolerated. OC-012 added a `metadata: provider: google` guard as a stopgap. FR-178 was needed to remove the root cause.

**symptom_patch**: The metadata guard was a symptom patch. The root cause was the LLM call inside a Python tool. Normalizing at the boundary (YAML llm node) was the correct fix.

## What I learned

The three-layer architecture is a constraint, not a guideline. When Python tools call `execute_prompt()`, they become invisible to graph-level observability (LangSmith traces the Python invocation, not the LLM span). The YAML llm node makes the call visible and auditable.

The `merge_extraction` split also makes testing cleaner: no mocking of `execute_prompt`, just stubbing `extraction_result` in state.

## Seed

If a future use case requires a dynamic schema per probe (one Pydantic model per `target_fields` set), what is the minimal YAML/framework extension that would support it without forcing LLM calls back into Python? Could `schema_from_state` be a first-class node option?
