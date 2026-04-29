# 2026-04-29 — Reflection: FR-299 Promptfoo Router Eval Demo

## What happened

Implemented the Promptfoo evaluation demo for the YAMLGraph router graph. Created `examples/demos/promptfoo-router/` with a Python provider bridge (`provider.py`), Promptfoo configuration, and three test suites (classification accuracy, response quality via LLM-as-judge, edge cases). All 11 test cases pass at 100%.

## Cognitive process

The FR was well-specified with file structure, code snippets, and acceptance criteria. Enforcement was largely mechanical — copy the router graph/prompts, write the provider bridge, wire Promptfoo config, create test cases.

Two corrections required during enforcement:

1. **Provider mismatch**: The original router demo uses `provider: xai`, but no `XAI_API_KEY` was available. Switched the demo copy to `provider: openai` with `gpt-4o-mini`. This is the right call — the demo should use the most commonly available API key.

2. **Classification type assumption**: The FR's `provider.py` code assumed `result["classification"]` would be a dict with `.get('tone')`. In practice, the router node stores the route field value as a plain string (e.g., `"positive"`). Added isinstance check to handle both dict and string forms.

## Traps avoided

- **downstream_fix**: The classification type mismatch was caught by running `invoke_graph` directly and inspecting the actual return structure before debugging through Promptfoo's abstraction layer. Normalize at the boundary (provider.py) where external data enters.
- **intent_drift**: FR specified `xai` provider but the execution environment had no `XAI_API_KEY`. Rather than hunting for the key, adapted the demo to use what's available. The demo's value is the Promptfoo pattern, not the specific LLM provider.

## Seed

Could the Python provider bridge be generalized into a `yamlgraph-promptfoo` package that auto-discovers state keys and generates assertion skeletons from graph schema definitions?
