# Reflection: FR-390 watcher2 sanity-check state (watcher2 post-validate sanity review)

**Date:** 2026-05-14
**FR:** FR-390 — watcher validate-fix context normalization and sanity-check timeout budget
**Reviewer:** watcher2 (post-validate sanity reviewer)

## Trap

`downstream_fix` — the original code had a prompt-level guard filtering out `{precommit_output}` literals in the rendered YAML prompt, treating the symptom downstream rather than normalizing at the action boundary where external context meets the command builder.

## What Happened

Two post-enforce reliability failures were confirmed in watcher pipeline v2:

1. **Context normalization gap**: `validate_fix` was invoked with literal `{precommit_output}` / `{validate_gate_output}` placeholder strings as `--var` arguments when those keys were absent from context on first-pass execution. The `yamlgraph_async_action.py` builder preserved unresolved `{key}` tokens as-is. A prompt-level heuristic existed but operated downstream of the boundary — a classic `downstream_fix` trap.

2. **Timeout budget mismatch**: `sanity_check` (pipeline action + graph node) had a 600s ceiling while the preceding `enforce_session` held 3600s. Real runs (FR review + diff inspection + diary write + commit) exceeded 10 minutes, causing avoidable post-success timeout failures observed in gh-382 and gh-383.

## Root Cause

- Action boundary (`yamlgraph_async_action.py` `_build_cmd_parts`) performed simple string replacement and passed through any unresolved `{placeholder}` tokens without normalization.
- Timeout values were set once during initial pipeline authoring and never revisited against observed runtime durations.

## What Worked

- **Boundary normalization at entry point**: Added `_is_placeholder()` (full-match regex) and `_NORMALIZE_EMPTY_ON_UNRESOLVED` set directly in `yamlgraph_async_action.py`. Unresolved full-placeholder tokens for known diagnostic vars now become empty strings before crossing into argv — matching the pattern already present in `validate_gate_action.py`.
- **Dual timeout fix**: Both pipeline config (`watcher-pipeline-v2.yaml`) and graph node (`sanity-check-session.yaml`) were updated to 1200s simultaneously, avoiding the partial-remediation anti-pattern.
- **Tight test suite**: Five behavioral acceptance tests (AC-01..AC-05) verify the argv content directly by intercepting `asyncio.create_subprocess_exec`, with no implementation-detail assertions. All 5 pass cleanly.

Minor observation: the changelog fragment uses `type: feat` while the FR metadata declares `Type: Bug`. For fix-class defects, `type: fix` would be more accurate — this is a cosmetic inconsistency but does not affect behavior.

## Seed:

> When a boundary normalization set (`_NORMALIZE_EMPTY_ON_UNRESOLVED`) is hardcoded with known var names, future additions require code changes to stay protected. Could the action config declare which vars are "diagnostic-optional" (defaulting to empty when unresolved), eliminating the need to maintain a static set?
