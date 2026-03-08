# Reflection: FR-162 Vulture Dead Code Cleanup

**Date:** 2026-03-08
**FR:** FR-162

## Context

Vulture pre-commit hook ran with `--min-confidence 80` but still produced false positives — framework-invoked symbols (Pydantic validators, LangGraph checkpointers, MCP handlers) that appear unused but are called dynamically. The noise eroded trust in the tool.

## Changes

- Created `vulture_whitelist.py` documenting all false positives with explanations
- Removed genuinely dead code: `yamlgraph/utils/sanitize.py` (zero callers)
- Lowered threshold from 80 → 60 with clean pass
- Added guard test `test_dead_code_guard.py` to prevent regression
- Added CONF-126 for whitelist suppressions

## Trap: noise_fatigue

When static analysis tools produce false positives, developers learn to ignore them. The signal-to-noise ratio determines whether alerts get attention. Vulture flagging `model_validator` (invoked by Pydantic at runtime) trained us to assume all warnings were false.

## Cure: whitelist_with_commentary

Don't suppress silently. Create a whitelist file where each entry explains *why* it's a false positive. Future reviewers can then audit the whitelist itself. The documentation turns suppression from "ignore this" into "I verified this."

## Seed

Could the whitelist entries be auto-generated from framework decorators? `@model_validator` → auto-whitelist. This would shift maintenance from manual curation to decorator-based inference.
