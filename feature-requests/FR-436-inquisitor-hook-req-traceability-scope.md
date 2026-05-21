# Feature Request: FR-436 ADR-001 scope contract for hook tests

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-21

## Summary

Define and codify ADR-001 scope boundaries so requirement-tag enforcement is explicit: `tests/unit` and `tests/integration` require `@pytest.mark.req`, while `.github/hooks/tests` is treated as infrastructure test scope with documented rationale and explicit exclusion from framework REQ coverage.

## Value Statement

Maintainers get deterministic, audit-stable traceability rules that prevent repeated false violations about hook tests while preserving strict REQ-YG enforcement for framework capabilities.

## Problem

Inquisitor audits 244 and 245 (consecutive) flagged missing `@pytest.mark.req` tags in `.github/hooks/tests/`. The boundary is currently ambiguous:

1. `ARCHITECTURE.md` ADR-001 wording says every test must be tagged, but does not define scope tiers.
2. `scripts/req_coverage.py` scans only `tests/unit` and `tests/integration`.
3. `.github/hooks/tests/*` contains zero `@pytest.mark.req` markers and is executed via dedicated hook test commands in `.github/hooks/README.md`, outside `tests/conftest.py` collection enforcement.

This mismatch creates recurring audit drift: doctrine text appears global while enforcement is scope-limited.

### Evidence gathered

1. `scripts/req_coverage.py` hard-codes coverage roots to `tests/unit` and `tests/integration`.
2. `tests/conftest.py::pytest_collection_modifyitems` enforces markers only for tests collected under `tests/`.
3. `.github/hooks/tests/` currently contains six suites with no `@pytest.mark.req` markers:
   - `test_fr_checks.py`
   - `test_markdown_checks.py`
   - `test_pre_command_guard.py`
   - `test_python_checks.py`
   - `test_session_timeline.py`
   - `test_yaml_checks.py`
4. `ARCHITECTURE.md` already uses scoped traceability language elsewhere (`examples/` vs `projects/`), so a scope contract pattern exists.

## Objectives

1. Make ADR-001 scope explicit and unambiguous.
2. Align documentation, script behavior, and inquisitor audit prompts to the same boundary contract.
3. Eliminate repeat findings on hook-test req tags without weakening framework REQ-YG traceability.

## Constraints

1. Single responsibility: clarify and enforce traceability scope only.
2. No hook behavior changes (no modifications to hook decision logic).
3. Preserve strict REQ-YG enforcement for framework tests (`tests/unit`, `tests/integration`).
4. Do not introduce a new requirement namespace in this FR.

## Proposed Solution

1. **Define ADR-001 scope tiers in `ARCHITECTURE.md` (Requirement Traceability section).**
   - **Tier 1 (framework):** `tests/unit/`, `tests/integration/` → `@pytest.mark.req("REQ-YG-XXX")` required.
   - **Tier 2 (infrastructure hooks):** `.github/hooks/tests/` → explicitly exempt from REQ-YG marker mandate, with rationale that these validate hook operational guards, not framework capability requirements.
   - **Tier 3 (demo/proof docs):** no REQ marker mandate.
2. **Amend `docs/adr/001-test-requirement-traceability.md`** to include the same scope contract and rationale.
3. **Codify boundary in `scripts/req_coverage.py`** by making include scope explicit (framework test dirs) and documenting `.github/hooks/tests` exclusion in code and output/help text.
4. **Update `.chaplain/inquisitor.sh` audit prompt text** so “tests must have req tags” is evaluated using the scoped ADR contract rather than a blanket statement.
5. **Update `.github/hooks/README.md` testing section** with a short note that hook tests are infrastructure-scope and intentionally outside REQ-YG coverage.

## Acceptance Criteria

- [x] **AC-01:** `ARCHITECTURE.md` ADR-001 section defines explicit traceability tiers and names all three paths/scopes above.
- [x] **AC-02:** `ARCHITECTURE.md` row for REQ-YG-063 is updated to reflect framework-scope enforcement (`tests/` tree), not blanket “all tests”.
- [x] **AC-03:** `docs/adr/001-test-requirement-traceability.md` mirrors the same scope contract and rationale.
- [x] **AC-04:** `scripts/req_coverage.py` contains explicit framework include dirs and explicit `.github/hooks/tests` exclusion notes.
- [x] **AC-05:** `.chaplain/inquisitor.sh` prompt text checks req tags with scope-aware wording.
- [x] **AC-06:** `.github/hooks/README.md` documents the infrastructure-test traceability policy.
- [x] **AC-07:** New unit tests for the scope contract pass and protect against regression.

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr436_req_traceability_scope_red.py`

Planned RED tests:

1. `test_ac01_architecture_adr001_defines_traceability_tiers`
2. `test_ac02_reqyg063_wording_is_framework_scope_not_global`
3. `test_ac03_adr001_doc_mirrors_tier_contract`
4. `test_ac04_req_coverage_explicitly_scopes_and_excludes_hook_tests`
5. `test_ac05_inquisitor_prompt_uses_scope_aware_req_tag_check`
6. `test_ac06_hooks_readme_documents_infrastructure_scope_policy`

RED command:

```bash
pytest tests/unit/test_fr436_req_traceability_scope_red.py -q --no-cov
```

## Alternatives Considered

1. **Tag `.github/hooks/tests` with REQ-YG IDs**
   Rejected: would couple infrastructure hook checks to framework capability IDs and inflate CAP/REQ mappings without clear capability ownership.
2. **Introduce `REQ-INF-*` namespace now**
   Rejected: valid long-term option, but larger cross-cutting change (new registry/schema/coverage rules) than needed to resolve this ambiguity.
3. **Keep current implicit behavior**
   Rejected: repeats the same audit drift because docs and enforcement remain inconsistent.

## Judge Notes

**Date:** 2026-05-21
**Verdict:** APPROVE

**Rationale:**

1. **Problem is real and documented.** `scripts/req_coverage.py` already scopes to `tests/unit` + `tests/integration` (line 347). `tests/conftest.py::pytest_collection_modifyitems` only fires for items collected under `tests/`. Hook tests at `.github/hooks/tests/` are correctly excluded from both mechanisms. The bug is in the specification: REQ-YG-063 says "all tests must have `@pytest.mark.req`" and `inquisitor.sh` uses the same unscoped wording — causing repeated false audit findings (244, 245).

2. **Scope is clear and minimal.** Pure documentation + comment alignment. No hook behavior changes, no new namespace, no new capability required.

3. **Acceptance criteria are measurable.** Each AC targets a specific file/section with verifiable content changes. RED tests are doc-content assertions (file contains required text) that will fail before edits land and pass after.

4. **Classification:** Bug fix / doc clarification. Enforcement behavior is already correct; specification is wrong. The fix closes the specification-to-implementation gap without expanding scope.

5. **AC-07 test quality is acceptable.** Tests check for *substantive* wording ("Tier 1", "Tier 2", infrastructure rationale, explicit exclusion note) — not just file presence. This satisfies substance-over-presence principle.

**Scope frozen. Authority granted to implement.**

## Related

- Topic: `.chaplain/processing/inquisitor-hook-req-tags.md`
- `ARCHITECTURE.md` (Requirement Traceability / REQ-YG-063)
- `docs/adr/001-test-requirement-traceability.md`
- `scripts/req_coverage.py`
- `tests/conftest.py`
- `.chaplain/inquisitor.sh`
- `.github/hooks/README.md`
- `.github/hooks/tests/`
