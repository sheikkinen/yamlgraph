# FR-120: Update FR-112 Status Draft → Implemented

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 5 min
**Requested:** 2026-03-07

## Summary

FR-112 (Inception Labs Mercury-2 Provider) shipped in v0.4.60 on 2026-03-06 with full implementation, tests, and CHANGELOG entry, but its status field still reads "Draft". The Inquisitor has flagged this as a violation in eight consecutive audits (I–VIII), and it was formally accepted as a known deviation in Audit VIII with a v0.5.0 deadline. Still unfixed as of Audit X.

## Value Statement

Maintainers and the Inquisitor get an accurate project status, eliminating a persistent audit violation that has polluted eight consecutive audit reports.

## Problem

`feature-requests/FR-112-inception-provider.md` line 3 reads:

```
**Status**: Draft
```

This contradicts reality: the feature is fully shipped. The stale status:

1. Triggers a ✗ VIOLATION in every Inquisitor audit, adding noise to audit reports.
2. Misleads anyone reading the feature request about its actual state.
3. Violates the doctrine: "let the CHANGELOG bear witness to the evolution of the Word" — the CHANGELOG says shipped, the FR says Draft.

## Proposed Solution

In `feature-requests/FR-112-inception-provider.md`, line 3, change:

```markdown
**Status**: Draft
```

to:

```markdown
**Status**: ✅ Implemented (v0.4.60)
```

No other files require changes. The implementation, tests, and CHANGELOG entry already exist from the v0.4.60 release.

## Judgement

**Verdict: APPROVED** — 2026-03-07

Scope is frozen. Authority granted to implement.

**Findings:**
1. ✅ Scope is minimal — single field change in one file.
2. ✅ No contradictions — CHANGELOG v0.4.60 confirms FR-112 shipped.
3. ✅ Acceptance criteria are measurable and verifiable.
4. ✅ Implementation is trivial and risk-free.
5. ✅ Aligns with existing architecture — follows the `✅ Implemented (vX.Y.Z)` convention.

**Amendment applied:** Status target updated from `Implemented` to `✅ Implemented (v0.4.60)` to match the convention used by recent shipped FRs (FR-024, FR-025, FR-026, etc.).

## Acceptance Criteria

- [ ] `feature-requests/FR-112-inception-provider.md` status field reads `Implemented`
- [ ] Inquisitor audit no longer flags FR-112 status as a violation
- [ ] Commit message follows convention: `chore(FR-112): FR-120 update status Draft→Implemented`

## Alternatives Considered

- **Status: Done** — Rejected. The codebase convention uses "Implemented", not "Done".
- **Add Implemented/Judged date fields** — Out of scope for this micro-fix; the dates are recoverable from git history and CHANGELOG if needed later.
- **Do nothing** — Unacceptable. Eight consecutive audit violations is a process smell per the diary trap `audit_as_ritual`: "3+ audits without fix → ritual, not process."

## Related

- `feature-requests/FR-112-inception-provider.md` — the stale file
- `CHANGELOG.md` — v0.4.60 entry confirming FR-112 shipment
- FR-118 (Inquisitor Auto-Propose) — cited FR-112 status as evidence of persistent audit violations
