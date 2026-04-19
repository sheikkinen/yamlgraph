## 2026-04-19: Inquisitor Audit — Confession ID Collisions

**Context:** Audited the 5 most recent commits on `main` (8dfb4039..8d1465a9) covering FR-241 worktree self-heal, chatterbox multilingual fix, FR-242 changelog cross-wiring correction, and two FR planning docs (FR-244, FR-245). Checked Conventional Commits, changelog fragments, req traceability, diary reflections, and noqa confessions.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits format. `fix` commits reference PR numbers; FR-scoped commits include FR-XXX identifiers.
- ✓ COMPLIANT — Changelog fragments exist for all `fix` PRs (#110 fr-241, #111 fix-chatterbox, #112 fr-242). Tests in FR-241 and FR-242 carry `@pytest.mark.req` tags.
- ✓ COMPLIANT — Diary reflections exist for FR-241 and FR-242. Both extract cognitive traps (`plausible_wrong_answer`, copy-paste drift) and plant forward-looking seeds.
- ⚠ DRIFT — Chatterbox fix (#111) has no diary entry. The diary-gate only enforces for FR-referenced PRs, so CI passed. The fix is a one-line guard removal — minimal cognitive surface. Related FR-239 diary covers the broader multilingual work. Low risk but sets a precedent of undocumented fixes.
- ✗ VIOLATION — 4 duplicate CONF IDs in `docs/confessions.md`: CONF-007 (lines 91 + 127), CONF-008 (lines 97 + 133), CONF-035 (lines 145 + 373), CONF-036 (lines 151 + 379). Each pair maps to completely different files, codes, and rationales. This breaks the traceability contract — a CONF-XXX ID no longer uniquely identifies a suppression. Root cause: FR-222 (security rules) added new confessions reusing IDs already claimed by the C901 complexity section above. FR-241 added worktree confessions reusing IDs from the test section below.

**Heuristic:** Confession IDs are an append-only monotonic sequence. Any process that adds confessions must scan for `max(CONF-XXX)` before assigning new IDs — same boundary-normalization principle as req IDs. A pre-commit check that validates CONF-ID uniqueness would prevent recurrence.

**Seed:** Should the pre-commit `dependency-rationale` hook pattern be extended to enforce CONF-ID uniqueness in `docs/confessions.md`, blocking commits that introduce duplicate confession identifiers?
