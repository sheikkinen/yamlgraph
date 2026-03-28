## 2026-03-15: Inquisitor Audit — Post-EXIF Metadata & Map Subgraph Compliance

**Context:** Audited the 5 most recent commits on `main` (`52661ec`..`74c078c`), covering FR-202 image pipeline delivery, map-over-subgraph extension, EXIF metadata embedding, and dict-prompt fix. Assessed Conventional Commits, ADR-001, changelog, diary, and noqa confessions.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits.** All 5 commits follow `type(scope): description`. Both `feat` commits reference FR-202. The `docs` commit correctly omits FR reference.

2. ✓ **COMPLIANT — Changelog fragments.** All `feat`/`fix` commits have corresponding fragments in `changelog/unreleased/`: `feat-map-over-subgraph.md`, `FR-202-image-generation-pipeline.md`, `fix-image-pipeline-dict-prompts.md`, `fix-exif-only-metadata.md`. The `docs` commit correctly has none.

3. ⚠ **DRIFT — REQ tag points downstream of framework change (persistent from audit-134).** `42e5236` extends core `map_compiler.py` to handle `NodeType.SUBGRAPH` in map iteration — a framework capability. All tests tag `REQ-YG-198` (image pipeline example) rather than `REQ-YG-040` (map node compilation). The change is tested and traced, but the req link misses the actual boundary. This was flagged in audit-134 and remains unaddressed.

4. ✓ **COMPLIANT — Diary and noqa confessions.** `docs/diary/2026-03-15-reflection-fr-202.md` covers the full FR-202 scope including the fix commits. All `# noqa` suppressions in `yamlgraph/` and `tests/` have corresponding CONF-XXX entries in `docs/confessions.md`.

5. ✓ **COMPLIANT — New tests have req tags.** `52661ec` added `test_no_sidecar_when_exif_succeeds` and `test_writes_sidecar_when_exif_fails` inside `TestGenerateImagesNode` which carries class-level `@pytest.mark.req("REQ-YG-198")`.

**Heuristic:** When a drift finding persists across consecutive audits without remediation, the Inquisitor should escalate from ⚠ DRIFT to ✗ VIOLATION on the third occurrence. Two consecutive audits flagging the same issue without action indicates the finding is being ignored, not deferred. **Stale drift is silent erosion.**

**Seed:** Should the Inquisitor auto-generate a lightweight FR (or inbox proposal) when the same drift finding appears in 3+ consecutive audits, triggering the Chaplain enforce pipeline to remediate it?
