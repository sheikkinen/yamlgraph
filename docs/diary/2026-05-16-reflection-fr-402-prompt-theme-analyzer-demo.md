# Reflection: FR-402 Prompt Theme Analyzer Demo

**Date:** 2026-05-16
**FR:** FR-402

## What changed

Implemented a complete demo for prompt theme analysis using the canonical
`list -> map -> aggregate -> group -> write` shape. The critical correction was
keeping normalization at ingress: `list_prompts` now enforces required
`source_dir`, filters invalid prompt payloads, and truncates text before map
fan-out.

## Cognitive trap and correction

**Trap:** `downstream_fix` — trying to solve prompt size and noise in prompt
templates or grouping nodes.
**Correction:** normalize once at the Python boundary before LLM interaction so
later nodes only process bounded, valid inputs.

## Heuristic

When a map node may fan out to hundreds of items, pair it with deterministic
aggregation before any second-stage LLM reasoning.

## Seed

Seed: Should YAMLGraph provide a reusable built-in reducer for "label -> count"
aggregation to standardize this map-to-aggregate pattern across demos?
