# Reflection: FR-252 Python Node Variables

**Date:** 2026-04-19
**FR:** FR-252
**Branch:** feat/fr-252-python-node-variables

## What Was Done

Extended `type: python` nodes with `variables:` expression resolution, making them consistent with LLM, router, and other node types that already support `{state.field}` interpolation. The implementation reuses the existing `resolve_node_variables()` utility from `yamlgraph/utils/expressions.py`, keeping the change minimal — a single conditional block in `create_python_node()`. Added 6 unit tests covering resolution, state injection, literal passthrough, missing field errors, mixed expressions, and empty variables. Removed the obsolete W020 lint rule that had blocked this capability.

## Cognitive Trap: Consistency as a Feature

The trap here was treating `variables:` support as a "nice to have" rather than a consistency requirement. Every other node type already resolved expressions, so python nodes silently diverging created a **false expectation boundary** — users writing YAML graphs would naturally assume `variables:` works everywhere, and the failure mode was silent (variables simply wouldn't resolve, and the function would receive the raw template string). This is a form of the **plausible wrong answer** trap: the graph runs without error, but the python function receives `"{state.url}"` instead of `"https://example.com"`.

The cure was straightforward: reuse the existing boundary normalization (`resolve_node_variables`) rather than inventing a new mechanism. The cheapest code is unwritten code — and in this case, the implementation was essentially a 6-line conditional wrapping an existing utility.

## Heuristic

**Feature parity is a boundary contract, not a convenience**: When a capability exists for most node types but not all, the missing type is a latent defect. The graph YAML contract promises uniform behavior across node types; selective omission breaks that contract silently. Audit new capabilities against all node types at design time, not after user reports.

## Seed

Could the graph linter automatically detect when a node config uses a key (like `variables:`) that is valid for other node types but not the current one, and emit a warning? This would surface feature-parity gaps at lint time rather than runtime.
