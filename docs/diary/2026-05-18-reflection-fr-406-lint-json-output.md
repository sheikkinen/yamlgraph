# Reflection — FR-406 Machine-Readable Lint Output

**Date:** 2026-05-18
**FR:** FR-406
**Scope:** `yamlgraph/cli/graph_validate.py`, `yamlgraph/cli/__init__.py`

## What happened

Added `--json` flag to `yamlgraph graph lint` so automation consumers get NDJSON output instead of human-formatted emoji text. The structured `LintResult` model already existed in the linter module — this was purely a transport-layer change at the CLI boundary.

## Cognitive process

The implementation was straightforward because the boundary was already well-defined: `graph_linter.py` returns Pydantic models, and the CLI layer serializes them. The only design decision was output format (NDJSON vs array) — NDJSON won because it allows streaming one result per file without buffering the entire run, matching the existing `graph run --json` precedent.

## Trap encountered

**Downstream fix** — Initial instinct was to add JSON formatting logic deep inside the linter module. Caught it early: the linter's job is to produce structured diagnostics, not to know about serialization formats. The CLI layer (presentation) owns format selection. Normalize at the boundary.

## Insight

When structured data already exists in memory (Pydantic models), adding a machine-readable output mode is trivial — just expose what's already there. The expensive work was done when the linter was originally built with typed models instead of ad-hoc dicts. Good boundaries pay forward.

## Seed

Seed: **Could `graph lint --json` feed directly into a SARIF converter for IDE integration?** The NDJSON schema is close to SARIF's `result` object shape. A thin mapping layer could enable VS Code problem-matcher integration without changing the linter itself — pure presentation-layer concern.
