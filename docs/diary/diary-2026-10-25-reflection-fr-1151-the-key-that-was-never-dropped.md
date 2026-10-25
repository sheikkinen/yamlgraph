# Reflection: FR-1151 — the key that was never dropped

**Date:** 2026-10-25
**FR:** FR-1151 (an `effort` setting for Anthropic llm nodes)

## What happened

The FR began from a claim made earlier in the day: yamlgraph silently drops an `effort:` key on a node. The judge
built on it: its R-2 asked that `effort` be refused on race nodes "where it would be silently dropped". Writing the
first test, I went looking for where nodes are validated, briefly concluded that `NodeConfig` never runs at load,
then found that it does (`validate_graph_schema`, FR-673) and that it is `extra: forbid`. A probe settled it. On a
node, `effort: low` is refused today with "Extra inputs are not permitted". Only `defaults.effort` loads and does
nothing. The design survived; the premise did not, and the FR carries a dated correction.

The build then met five gates in turn: the size gate (an import wrapped to five lines), the radon gate (one `if`
pushed `create_llm` from C to D), vulture (a Pydantic validator looks unused), ruff on a whitelist nobody had touched
since FR-1125 (two bare names), and the line-keyed confessions that every insertion shifts. Each needed a small,
recorded change outside the judged scope.

## Root cause

The first claim was an inference from reading the factory signature ("nothing else reaches the API"), stated as an
observation about the loader. Both halves were believed because the first half was true.

## Heuristic

**Before an FR states how the system treats an input, feed it that input.** A one-file graph and one load call cost
seconds; the FR, the judge and the tests all inherit whatever the Problem section says.

Second: **line-keyed allowlists tax every insertion above them.** Six hedging keys and two noqa anchors moved for
fifteen added lines; the fixer repaired none of the noqa ones.

## Corrective actions

- `effort` on defaults, `llm` and candidate-less `router` nodes, to `output_config.effort`; refused elsewhere.
- The Problem correction, the RED and GREEN record, the live call and five scope deviations in the FR.

**Seed:** Should hedging and noqa confessions be keyed by a symbol (function or field name) instead of a line, so a
feature that inserts lines above them stops being a change to `docs/confessions.md`?
