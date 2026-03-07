# Feature Request: Fix ARCHITECTURE.md provider count drift

**Priority:** LOW
**Type:** Bug
**Status:** Completed
**Effort:** < 1 hour
**Requested:** 2026-03-07

## Summary

The ARCHITECTURE.md module table row for `utils/llm_factory.py` read "7 providers" while the code (and the same document's overview section) reflected 8 providers after Inception was added. A one-character fix (`7` → `8`) plus a guard test (REQ-YG-121) close the loop.

## Value Statement

Maintainers can trust ARCHITECTURE.md provider counts because an automated test fails when code and docs diverge.

## Problem

After the Inception provider was added to `ProviderType`, only the overview table (line ~219) was updated to "8 providers." The module table (line ~1143) was missed, leaving it at "7 providers." This was flagged as a ✗ VIOLATION in Inquisitor Audits I–VIII (8 consecutive audits) before resolution.

Root cause: no automated guard existed to detect documentation-count drift.

## Proposed Solution

Two-part fix (both already landed):

1. **One-character doc fix** — Change "7 providers" → "8 providers" in the module table row (commit `55b890b`).

2. **Guard test (REQ-YG-121)** — `tests/unit/test_architecture_provider_count.py` extracts the count from the module table via regex and asserts it equals `len(get_args(ProviderType))`. A companion smoke test asserts the exact set of known providers, catching both additions and removals.

## Acceptance Criteria

- [x] ARCHITECTURE.md module table row for `llm_factory.py` says "8 providers"
- [x] ARCHITECTURE.md overview section says "8 providers"
- [x] `test_module_table_provider_count_matches_code` passes (REQ-YG-121)
- [x] `test_provider_type_has_expected_providers` passes (REQ-YG-121)
- [x] Adding/removing a provider without updating ARCHITECTURE.md causes a test failure

## Alternatives Considered

- **Manual audit enforcement only** — rejected; 8 consecutive audit violations prove manual-only checks are insufficient.
- **Pre-commit hook instead of pytest** — possible but adds complexity; a unit test is simpler and already runs in CI.

## Related

- Commit `55b890b` — `docs: update provider count to 8 (add Inception)`
- Requirement `REQ-YG-121` in ARCHITECTURE.md
- Test: `tests/unit/test_architecture_provider_count.py`
- Inquisitor Audits I–VIII (provider count violation)
