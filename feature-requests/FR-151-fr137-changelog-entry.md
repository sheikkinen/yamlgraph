# Feature Request: FR-137 Missing CHANGELOG Entry

**Priority:** HIGH
**Type:** Bug
**Status:** ✅ Implemented
**Effort:** 0.25 days
**Requested:** 2026-03-08

## Summary

Add the missing CHANGELOG entry for FR-137 (DeepSeek provider), which merged to `main` without one — violating Commandment 10 across two consecutive audits (XXXIV, XXXV).

## Value Statement

Maintainers and users get an accurate release history, and the two-audit CHANGELOG violation is resolved.

## Problem

FR-137 added DeepSeek as the ninth LLM provider — a standalone `feat` with its own FR number, ARCHITECTURE.md updates, and tagged tests — yet CHANGELOG.md has zero mention of DeepSeek or FR-137. This was flagged as ✗ VIOLATION in Audit XXXIV and again in Audit XXXV (two consecutive audits without remediation).

Commandment 10: *"let the CHANGELOG.md bear witness to the evolution of the Word."*

FR-149 (CI CHANGELOG gate) will prevent future recurrences; this proposal fixes the existing gap.

## Proposed Solution

Add a single line under `[Unreleased] → Added` in CHANGELOG.md:

```markdown
- **FR-137 DeepSeek Provider**: Added DeepSeek as ninth LLM provider via `create_llm(provider="deepseek")`. Requires `DEEPSEEK_API_KEY` environment variable.
```

Insert it in FR-number order among the existing entries (after FR-138, before FR-136).

## Acceptance Criteria

- [x] CHANGELOG.md `[Unreleased] → Added` contains an entry referencing FR-137 and DeepSeek
- [x] Entry describes the provider addition and required environment variable
- [x] Entry is positioned in descending FR-number order consistent with surrounding entries
- [x] `grep -c "FR-137" CHANGELOG.md` returns ≥ 1

## Alternatives Considered

- **Wait for next release**: Rejected — two audits already flagged this; further delay compounds the violation.
- **Backfill into 0.4.60**: Rejected — FR-137 merged after 0.4.60; entry belongs in `[Unreleased]`.

## Related

- `feature-requests/FR-137-deepseek-provider.md` — the approved FR that merged without a CHANGELOG entry
- `feature-requests/FR-149-ci-changelog-gate.md` — CI gate to prevent future recurrences
- `.chaplain/inbox/inquisitor-fr137-changelog.md` — inquisitor violation report (Audits XXXIV–XXXV)
