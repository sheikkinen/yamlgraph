## 2026-03-08: Inquisitor Audit XXXII — Phantom Requirements and Missing Trailers

**Context:** Thirty-second audit. Examined 5 most recent commits on `main` (`6bcdfa8..0c74848`): FR-139 bare=true corruption guard, FR-140/diary housekeeping, FR-134 post-merge finalization, and FR-134 diary folder refactor. Audited against Conventional Commits, Co-authored-by trailers, ADR-001 requirement traceability, diary reflections, and noqa confessions.

**Findings:**

1. **✗ VIOLATION — FR-139 tests use phantom requirement `REQ-YG-UTIL` (ADR-001).** Commit `0c74848` adds tests tagged `@pytest.mark.req("REQ-YG-UTIL")` but this requirement ID is not defined in `ARCHITECTURE.md` nor registered in `scripts/req_coverage.py`. The tag creates an illusion of traceability — tests appear compliant but the requirement doesn't exist. ADR-001 demands every `@pytest.mark.req` links to a real requirement.

2. **✗ VIOLATION — 3 of 5 commits missing Co-authored-by trailer.** Commits `0c74848`, `54b3d73`, `82c8b74` lack the required `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` trailer. Only `339598d` and `6bcdfa8` include it. The custom instructions mandate this trailer on every commit.

3. **⚠ DRIFT — FR-139 diary reflection missing (Sermon: Distill).** Feature `feat(worktree): FR-139` is complete and merged but no `reflection-fr-139.md` exists in `docs/diary/`. The Distill obligation requires a metacognitive entry after completing a feature.

4. **⚠ DRIFT — FR-134 reflection stub unfilled (5th consecutive audit).** First flagged in Audit XXVIII, now XXXII. Five audits confirming the same gap graduates this from drift to the `audit_as_ritual` trap: flagging without fixing is ritual, not process. `finalize_merge.sh` creates stubs but no one fills them.

5. **✓ COMPLIANT — Conventional Commits, CHANGELOG, and noqa discipline.** All 5 commits follow `type(scope): description` format. `feat` commits reference FR numbers. FR-139 CHANGELOG entry present. The S603 noqa in `diary_rotate.py` is properly confessed as CONF-206.

**Heuristic:** *A phantom requirement is worse than no requirement.* `REQ-YG-UTIL` as a catch-all tag satisfies the syntactic check (`@pytest.mark.req` present) while defeating the semantic purpose (traceability to a defined capability). Either define `REQ-YG-UTIL` in `ARCHITECTURE.md` with explicit scope, or assign each utility test to its actual parent capability's requirement ID.

**Seed:** Should `req_coverage.py --strict` be extended to reject requirement IDs that appear in test markers but are not defined in `ARCHITECTURE.md` — making phantom requirements a CI failure rather than an audit finding?
