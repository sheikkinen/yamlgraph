# FR-185: Root Logger Respects LOG_LEVEL

**Date:** 2026-03-13
**Feature:** FR-185 — Root Logger Log Level

## What Happened

Arrived to find the feature fully implemented: `setup_logging()` in `yamlgraph/utils/logging.py` already configures the root logger after the `yamlgraph` namespace logger, setting its level and conditionally adding a `StructuredFormatter` handler. The tests in `tests/unit/test_logging.py` covered all three new behaviors (level set, handler added when none exists, handler not duplicated). All 17 tests passed green on first run.

## Cognitive Trap Encountered

**working_system_inertia**: The FR status header said "Implemented" but the acceptance-criteria checkboxes were unchecked — a subtle inconsistency. The temptation was to assume something was missing and start adding code. The correct move was to run the tests first and let the green suite confirm completeness before touching production code.

## Heuristic

> When a feature is claimed "Implemented" but criteria are unchecked, run the tests before writing a single line — green proves the claim; red reveals the gap.

## Seed

If `setup_logging()` is called multiple times (e.g., once at import and once from the CLI after parsing `--log-level`), the root logger level is updated but the existing root handler's formatter may not reflect the new `use_json` setting. Should `setup_logging()` update formatter on an existing root handler, or is one-time-at-import the intended contract?
