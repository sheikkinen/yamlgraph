## 2026-04-19: Inquisitor Audit — FR-237 numbering collision and recent commit compliance

**Context:** Audited the 5 most recent commits (`8743a380`..`53197254`) covering FR-069 (per-node timeout), FR-237 (race/pipeline docs + chatterbox consolidation), and FR-238 (pipeline accumulated state docs). Checked Conventional Commits format, changelog fragments, ADR-001 traceability, `@pytest.mark.req` tags, diary reflections, and noqa confessions.

**Findings:**

1. **✗ VIOLATION — FR-237 numbering collision.** Two distinct feature requests share FR-237: "Chatterbox Consolidate and CLI" (`FR-237-chatterbox-consolidate-and-cli.md`) and "Document Race and Pipeline Node Types" (`FR-237-document-race-and-pipeline-node-types.md`). Same ID, different work items. Traceability is broken — `git log --grep FR-237` returns unrelated commits. Action: renumber one FR and update all references (changelog fragment, diary, capability file, tests).

2. **⚠ DRIFT — Wrong REQ in changelog fragment.** `changelog/unreleased/fr-237-document-race-and-pipeline-node-types.md` declares `req: REQ-YG-238` (Chatterbox speak CLI) instead of `req: REQ-YG-240` (race/pipeline docs). ARCHITECTURE.md CAP-99 and `test_race_pipeline_docs.py` correctly reference REQ-YG-240. The changelog fragment is inconsistent.

3. **✓ COMPLIANT — FR-069 per-node timeout (commit `3deb6165`).** Full doctrine compliance: Conventional Commits with FR reference, changelog fragment, ARCHITECTURE.md updated (CAP-97 → REQ-YG-078), all tests tagged `@pytest.mark.req("REQ-YG-078")`, diary reflection written, demo-output.log present.

4. **✓ COMPLIANT — Conventional Commits format.** All non-merge commits follow `type(scope): description`. The merge commit (`53197254`) is a local branch sync — squash merge at PR level produces the canonical message. No violations.

5. **⚠ DRIFT — No diary reflection for docs PR #105.** The `docs(reference): FR-237` commit included `2026-04-19-git-report.md` (a summary, not a reflection) but no metacognitive diary entry. `docs` PRs aren't gated by diary-gate CI, but the Sermon calls for distillation after completing a task list.

**Heuristic:** FR numbers are identifiers, not labels — a collision silently poisons every traceability query downstream. When the next available FR number is ambiguous, check `ls feature-requests/ | sort -t- -k2 -n | tail -1` before assigning.

**Seed:** Should `scripts/req_coverage.py` (or a new pre-commit hook) detect duplicate FR numbers across `feature-requests/` filenames and fail on collision, preventing this class of traceability error at commit time?
