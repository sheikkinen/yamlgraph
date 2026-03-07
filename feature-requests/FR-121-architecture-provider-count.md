# FR-121: Architecture Provider Count Drift Guard

**Status:** In Progress
**Priority:** Low
**Effort:** XS (< 1 hour)

## Problem Statement

ARCHITECTURE.md module table (line ~1134) claims `llm_factory.py` supports "7 providers"
but the actual `ProviderType` Literal in code lists 8. This drift was introduced when
the Inception provider was added (FR-112) — the ASCII diagram was updated but the module
table was not (partial remediation trap). Eight consecutive inquisitor audits flagged
this but no automated guard existed.

## Objective

Add a cross-check test that extracts the provider count from ARCHITECTURE.md and
compares it to the actual `ProviderType` Literal, preventing future drift.

## Acceptance Criteria

- [ ] Test reads `ProviderType` args and counts them
- [ ] Test parses ARCHITECTURE.md module table for `llm_factory.py` provider count
- [ ] Test fails if counts differ
- [ ] ARCHITECTURE.md updated from "7 providers" to "8 providers"
- [ ] REQ-YG-121 registered in ARCHITECTURE.md, `req_coverage.py`, and CAPABILITIES

## Implementation

1. **RED**: `tests/unit/test_architecture_provider_count.py` — fails on "7 ≠ 8"
2. **GREEN**: Fix ARCHITECTURE.md line 1134
3. **REGISTER**: Add REQ-YG-121 to requirement tables and coverage script

## Judgement

Scope is minimal and well-defined. The test guards a known recurring drift.
Freeze scope. Proceed.
