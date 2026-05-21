# Reflection: FR-429 Post-Edit YAML Checks

**Date:** 2026-05-21
**FR:** FR-429 Post-Edit YAML Checks
**Author:** copilot enforce pass

## Trap

`gate_checks_shape_not_substance` - the hook gate existed and worked for Python, but YAML edits bypassed the same edit-time enforcement boundary and pushed failures to late-stage lint/commit cycles.

## What Happened

`post-edit-checks.sh` had an early exit for all non-Python files, so graph and prompt YAML changes were invisible to the hook. FR-429 replaced that blanket exit with file-type routing:

1. Python files keep existing checks unchanged.
2. Graph YAML (`nodes` + `edges`) now runs `yamlgraph graph lint`.
3. Prompt YAML under `prompts/` now gets YAML parse validation.
4. Non-target YAML files are skipped to avoid false positives.

## Root Cause

The original hook was implemented as a single-language guard. As the repository workflow shifted to YAML-first graph/prompt editing, the enforcement boundary did not move with the dominant edit surface.

## What Worked

- Kept scope narrow: only routing + existing linter invocation, no new lint rules.
- Used linter exit code instead of output matching, which is format-agnostic and stable.
- Added subprocess-based tests for all acceptance paths: graph valid/invalid, prompt valid/invalid, non-target YAML skip, and Python regression safety.
- Verified suite clean: `.github/hooks/tests/test_post_edit_checks.py` passed 24/24.

## Seed

Seed: Should hook routing be declarative (extension/path/predicate table) so FR-431 and future file-type checks can be added without expanding a monolithic shell conditional block?
