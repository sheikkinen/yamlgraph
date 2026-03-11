## 2026-03-11: Inquisitor Audit — FR-183/184 commit wave and traceability gaps

**Context:** Audited the latest 5 commits (b3f7d20..d1df27d) covering FR-183 enforce simplification, FR-184 philosopher daemon, FR-181 probe recap fix, FR-170 async action docs, and diary housekeeping.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the pattern (`feat(scope): FR-XXX`, `fix(scope): FR-XXX`, `docs(scope):`, `docs(diary):`). Scopes are present and FR references included where required.

2. ✗ VIOLATION — **REQ-YG-183 missing**: FR-183 (enforce pipeline simplification) added a changelog fragment and diary entry but has no REQ-YG-183 in `ARCHITECTURE.md`, no capability YAML file, and `test_enforce_simplify.py` uses generic tags (REQ-YG-001, REQ-YG-012) instead of a dedicated REQ-YG-183. FR-184 was correctly traced (REQ-YG-184, CAP-67). The asymmetry suggests FR-183 was treated as a refactor rather than a capability — but it ships changelog, tests, and a new graph topology, which qualifies it for traceability under ADR-001.

3. ✓ COMPLIANT — **Changelog fragments**: Both FR-183 and FR-184 have fragments in `changelog/unreleased/`. FR-181 likewise. `docs` commits correctly omit fragments.

4. ✓ COMPLIANT — **Diary entries**: FR-183/184 commit includes `2026-03-11-reflection-fr-183-fr-184.md` with Trap, Heuristic, and Seed sections. FR-181 has `2026-03-11-fr181-implementation.md`. Diary housekeeping commit (d1df27d) delivers chaplain and inquisitor entries.

5. ⚠ DRIFT — **noqa confessions intact but stale line references**: Both `executor_async.py:310` (ANN001) and `token_tracker.py:51` (ARG002) are confessed. Line numbers in `docs/confessions.md` may drift as files change — no automated sync exists. Low risk currently.

**Heuristic:** When a commit ships tests, a changelog fragment, and modified graph topology, it is a capability — not a "mere refactor." Apply ADR-001 traceability (REQ + CAP file) uniformly regardless of whether the change adds or simplifies.

**Seed:** Could `scripts/req_coverage.py` detect changelog fragments that reference FR-XXX numbers without a corresponding REQ-YG-XXX in ARCHITECTURE.md, closing the traceability gap at pre-commit time?
