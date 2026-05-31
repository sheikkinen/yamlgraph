# Feature Request: CAP retirement support in req_coverage.py

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 0.25 days
**Requested:** 2026-05-31

## Summary

Add `status: retired` support to CAP YAML files and teach `req_coverage.py` to exclude retired REQs from coverage checks. Establishes the retirement lifecycle pattern for capabilities.

## Value Statement

Capability retirement becomes a first-class operation — retired CAPs stay in the registry as historical record while their REQs stop blocking `--strict` checks.

## Problem

When a subsystem is retired (e.g., watcher2 via FR-317), its CAP files and REQ IDs remain in the registry. Deleting test files that covered those REQs causes `req_coverage.py --strict` to fail on the orphaned REQs.

Current workarounds are both bad:
- **Delete CAP files** — loses historical record that the capability existed and was delivered
- **Keep skipped tests** — 84 false skips drown real signals (FR-465's problem)

No CAP file currently has a `status:` field. `req_coverage.py` has no concept of retirement.

## Proposed Solution

### 1. CAP YAML schema: add optional `status` field

```yaml
# capabilities/CAP-130-watcher2-finalize-optimization.yaml
id: CAP-130
name: Watcher2 Finalize Pre-commit Optimization
status: retired  # NEW — optional, default: active
description: >
  Optimize watcher2 finalize step...
```

Valid values: `active` (default if omitted), `retired`.

### 2. req_coverage.py: filter retired capabilities

In `load_capabilities_from_registry()`, skip REQs from retired CAPs:

```python
for filepath in yaml_files:
    with open(filepath) as f:
        data = yaml.safe_load(f)

    # Skip retired capabilities
    if data.get("status") == "retired":
        continue

    cap_id = data["id"]
    # ... rest unchanged
```

### 3. Reporting: show retired CAPs separately

Add a summary line to `--strict` output:

```
Retired capabilities (excluded): CAP-130, CAP-132, CAP-133, CAP-134
```

## Acceptance Criteria

- [ ] CAP YAML files accept optional `status: retired` field
- [ ] `req_coverage.py` excludes REQs from `status: retired` CAPs in coverage checks
- [ ] `req_coverage.py --strict` passes when retired CAPs have no test coverage
- [ ] CAPs without `status:` field default to active (no existing CAP files need changes)
- [ ] Retired CAPs listed in summary output for visibility
- [ ] Tests added for retirement filtering logic

## Alternatives Considered

- **Delete CAP files on retirement** — simpler but loses registry history. As more subsystems retire, the historical record of what was built and when becomes valuable.
- **Add `retired: true` boolean** — less extensible than a `status` enum if we later need `deprecated`, `planned`, etc.

## Related

- FR-465: Delete retired watcher2 tests (blocked by this FR)
- FR-317: Watcher2 pipeline retirement
- FR-178: Append-Only Capability Registry (established CAP YAML pattern)

## Judgement

**Verdict: APPROVED with corrections.**

### Finding: Two existing retirement mechanisms must be reconciled

The FR assumes no retirement concept exists. **Wrong.** Two mechanisms already exist, both based on a "delete file + reserve ID" model:

1. `scripts/validate_capabilities.py` → `RETIRED_CAPS` dict (CAP-27, 29, 52, 58, 63) — blocks reuse of deleted CAP IDs
2. `tests/unit/test_capability_registry.py` → `test_no_retired_ids_in_registry()` — asserts no YAML file exists for retired IDs

FR-466 proposes a **conflicting** model: keep files with `status: retired`. If a CAP-130 YAML file exists with `status: retired`, the existing `test_no_retired_ids_in_registry` test will pass (it only checks the hardcoded set), but `validate_capabilities.py` treats the file as active. Two models coexisting = confusion.

### Correction: unify the models

The `status: retired` field replaces the hardcoded `RETIRED_CAPS` dict and the test's hardcoded set. Single source of truth in the YAML file itself.

**Changes required (3 files, not 1):**

1. **`scripts/req_coverage.py`** — filter `status: retired` CAPs from `all_reqs` (as proposed)
2. **`scripts/validate_capabilities.py`** — migrate `RETIRED_CAPS` dict entries to the YAML files themselves; `validate_file()` reads `status: retired` and skips field validation for retired CAPs (they don't need all required fields since the capability is defunct)
3. **`tests/unit/test_capability_registry.py`** — replace hardcoded `retired` set in `test_no_retired_ids_in_registry` with a check that reads `status:` from YAML files

### Correction: handle the 5 already-deleted CAPs

CAP-27, 29, 52, 58, 63 were already deleted (no YAML files exist). Two options:
- **a)** Recreate minimal YAML stubs with `status: retired` for historical record
- **b)** Keep the `RETIRED_CAPS` dict for ID reservation of deleted files, add `status: retired` as a second mechanism for files that still exist

Option (b) is simpler and doesn't require recreating deleted files. The `RETIRED_CAPS` dict stays as a "tombstone registry" for IDs with no file. `status: retired` handles files that exist but whose REQs should be excluded.

### Corrected Acceptance Criteria

- [ ] CAP YAML files accept optional `status: retired` field (default: active)
- [ ] `req_coverage.py` excludes REQs from `status: retired` CAPs in coverage/strict checks
- [ ] `req_coverage.py` prints retired CAP summary for visibility
- [ ] `validate_capabilities.py` treats `status: retired` files as valid (relaxed field requirements)
- [ ] `test_capability_registry.py` updated: retired-ID test reads `status:` field from YAML instead of hardcoded set
- [ ] `RETIRED_CAPS` dict in `validate_capabilities.py` preserved for tombstone IDs (CAP-27, 29, 52, 58, 63) that have no file
- [ ] Tests cover: retired CAP excluded from req coverage, retired CAP passes validation, active CAP unchanged
- [ ] No existing CAP file modified in this FR (retirement of watcher2 CAPs is FR-465's job)
