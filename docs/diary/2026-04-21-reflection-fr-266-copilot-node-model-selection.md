# Reflection: FR-266 Copilot Node Model Selection

**Date:** 2026-04-21
**FR:** FR-266
**Branch:** feat/fr-266-copilot-node-model-selection

## What Was Done

Extended copilot nodes to support the same `model` and `defaults.model` convention used by LLM nodes. The `NodeConfig` schema gained a `model` field, `_compile_copilot_node()` now passes `effective_defaults` to the factory, and `create_copilot_node()` resolves model with a clear priority chain: `cli_flags.model` > node-level `model` > `defaults.model` > omit (let Copilot CLI choose). Nine tests cover every priority combination.

## Cognitive Trap: False Duplicate

The initial temptation was to treat this as "just another parameter pass-through" — syntactically similar to how `cli_flags.model` already works. But the semantics differ: `cli_flags.model` is a Copilot CLI implementation detail (a flag), while `model` is a graph-level concept (a node config key). Conflating them would have missed the defaults resolution chain entirely. The `false_duplicate` trap: syntactic similarity ≠ semantic equivalence.

## Heuristic

**Match the abstraction layer, not the implementation**: When a higher-level concept (graph config) wraps a lower-level mechanism (CLI flag), expose the concept at its natural layer. Don't force users to learn the implementation detail (`cli_flags.model`) when the abstraction (`model`) already exists for peer node types.

## Seed

Could the model resolution chain be unified across all node types (LLM, copilot, agent) into a single `resolve_model()` utility? Each node type currently implements its own priority logic — a shared resolver would eliminate drift and make the precedence rules testable in one place.
