# FR-122: Add FR-116 CHANGELOG Entry

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 5 min
**Requested:** 2026-03-07

## Summary

FR-116 (Watch→Enforce Integration) was implemented in commit `4765fdc` with full ADR-001 traceability (CAP-35, REQ-YG-116, 5 tagged tests, demo script) but has zero mention in `CHANGELOG.md` under `[Unreleased]`. Flagged in Inquisitor Audits VIII, IX, and X — three consecutive audits. Audit X escalated: "FR-116 CHANGELOG entry should block next release."

## Value Statement

Maintainers and the Inquisitor get accurate release notes, eliminating a persistent audit violation that has escalated across three consecutive audits to a release-blocking severity.

## Problem

`CHANGELOG.md` under `[Unreleased] → Added` has no entry for FR-116, despite the feature being fully shipped:

1. **Implementation:** `.chaplain/watch.sh` — `find`/`comm -13` FR detection + `nohup` spawn of `enforce_worktree.sh`
2. **Architecture:** CAP-35 in `ARCHITECTURE.md` with REQ-YG-116
3. **Tests:** `tests/unit/test_watch_enforce_spawn.py` — 5 test classes, all `@pytest.mark.req("REQ-YG-116")`
4. **Demo:** `examples/demos/watch-enforce/demo_detect.sh`
5. **Commit:** `4765fdc` — `feat: FR-116 implementation (#4)`

The missing entry:

1. Triggers a ✗ VIOLATION in every Inquisitor audit, adding noise to audit reports.
2. Means the next release will omit a shipped capability from its release notes.
3. Violates Commandment 10: "let the CHANGELOG bear witness to the evolution of the Word."
4. Matches the diary trap `audit_as_ritual`: "3+ audits without fix → ritual, not process."

## Proposed Solution

Add the following line to `CHANGELOG.md` under `[Unreleased] → Added` (after the existing FR-113 entry, line 11):

```markdown
- **FR-116 Watch→Enforce Integration**: `watch.sh` detects new feature requests after graph execution and auto-spawns `enforce_worktree.sh` via `nohup` for hands-free implementation. (REQ-YG-116)
```

No other files require changes. The implementation, tests, architecture docs, and demo already exist from commit `4765fdc`.

## Acceptance Criteria

- [ ] `CHANGELOG.md` `[Unreleased] → Added` section contains an entry for FR-116 describing the Watch→Enforce Integration
- [ ] Entry includes the requirement tag `(REQ-YG-116)`
- [ ] Inquisitor audit no longer flags FR-116 CHANGELOG as a violation
- [ ] Commit message follows convention: `docs(changelog): FR-122 add FR-116 watch→enforce entry`

## Alternatives Considered

- **Wait for next release** — Unacceptable. Three consecutive audit violations with release-blocking escalation means this is overdue, not premature.
- **Combine with other CHANGELOG fixes** — Rejected. Single responsibility: this FR addresses exactly one missing entry. Other audit violations have their own FRs (e.g., FR-120 for FR-112 status).
- **Do nothing** — Unacceptable. Audit X explicitly escalated this to release-blocking severity.

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted.

**Evaluation:**

1. **Scope clear and minimal?** — Yes. Single-line addition to `CHANGELOG.md`. No other files touched.
2. **Contradictions or ambiguities?** — One minor nit: the FR says "after the existing FR-113 entry, line 11" but FR-106 also sits under `Added` on line 12. Insert after *both* existing entries to preserve chronological order. Intent is unambiguous regardless.
3. **Acceptance criteria measurable?** — All four criteria are concrete and mechanically verifiable (grep for entry, grep for tag, run audit, check commit message).
4. **Implementation approach feasible?** — Trivially so. One line in one file.
5. **Alignment with architecture?** — Directly cures Commandment 10 violation and the `audit_as_ritual` diary trap. Three consecutive audit escalations make this overdue.

**Verified claims:**
- ✅ FR-116 is absent from `CHANGELOG.md` (confirmed via grep)
- ✅ Commit `4765fdc` exists with correct message
- ✅ All artifacts exist: `watch.sh`, tests (5 classes), demo, ARCHITECTURE.md (CAP-35/REQ-YG-116)
- ✅ FR-120 reference is valid

## Related

- `CHANGELOG.md` — the file missing the entry
- `.chaplain/watch.sh` — FR-116 implementation
- `ARCHITECTURE.md` — CAP-35 / REQ-YG-116 documentation
- `tests/unit/test_watch_enforce_spawn.py` — FR-116 test coverage
- `feature-requests/FR-120-fr112-status-update.md` — analogous audit-violation fix pattern
- Inquisitor Audits VIII, IX, X — escalation trail
