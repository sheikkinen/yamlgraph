---

## 2026-03-27: Inquisitor Audit — Image Pipeline Chore Commits & FR-203

**Context:** Audited the 5 most recent commits (ce1d082..52661ec): one `docs(FR)`, three `chore(examples)`, one `fix(examples)`. Scope covers image pipeline incremental improvements and the FR-203 five-whys-demo feature request.

**Findings:**

1. ✓ COMPLIANT — All 5 commits follow Conventional Commits format. Changelog fragment exists for the `fix` type commit. `chore`/`docs` types correctly omit fragments.

2. ✓ COMPLIANT — noqa suppressions in `yamlgraph/` (ANN001, ARG002) are both confessed in `docs/confessions.md` with CONF-IDs.

3. ✗ VIOLATION — **28 of 34 test functions in `tests/unit/test_image_pipeline.py` lack `@pytest.mark.req` tags.** ADR-001 mandates every test function carries a requirement marker. Only 6 functions (the standalone ones) are tagged; the 28 methods inside `TestGenerateImagesNode` are untagged.

4. ⚠ DRIFT — `fix(examples): embed prompt in EXIF metadata` (52661ec) bundles test changes and production fix in one commit. Commandment 7 prescribes separate RED (failing test) and GREEN (fix) commits. The original FR-202 RED commit (f6464d6) exists, but the fix-specific test updates were not committed separately.

5. ⚠ DRIFT — Three consecutive `chore(examples)` commits (9bb772b, e01eb18, e7d8202) incrementally improve image pipeline without diary entries. While `chore` type doesn't trigger diary-gate CI, the collective body of work (parallelization, timestamped filenames, extended EXIF) represents meaningful design decisions worth distilling.

**Heuristic:** Test classes inherit the file's import context but not its `@pytest.mark.req` decorator. When class-based tests grow organically (as `TestGenerateImagesNode` did across FR-202 and its fix), req tags on standalone functions create a false sense of coverage completeness. The `req_coverage.py` script counts tagged functions — class methods that lack tags are invisible to the audit. **Gate at the class level or enforce per-method.**

**Seed:** Should `req_coverage.py` report a warning when a test file contains a mix of tagged and untagged test functions, signaling incomplete traceability rather than silently passing on the tagged subset?
