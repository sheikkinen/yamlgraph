---

## 2026-03-27: Inquisitor Audit — Third Strike on Req-Tag Gap

**Context:** Audited the 5 most recent commits (e4a7d27..16e4973): two `docs(FR)` adding FR-203 and FR-204 feature requests, three `chore(examples)` extending the image pipeline (timestamps, parallelization, EXIF metadata enrichment). This is audit #141, following #140 which itself followed #139 — both flagging the same `test_image_pipeline.py` req-tag gap.

**Findings:**

1. ✓ COMPLIANT — All 5 commits follow Conventional Commits (`docs(FR):`, `chore(examples):`). No `feat`/`fix` types, so changelog fragments and diary-gate CI correctly not triggered.

2. ✗ VIOLATION (ESCALATED) — **28 of 34 test functions in `tests/unit/test_image_pipeline.py` lack `@pytest.mark.req` tags.** Commits e4a7d27 and 551a837 both modified this test file — adjusting assertions and adding test logic — without adding the missing req tags. Audits #139 and #140 flagged this identical violation. This is the **third consecutive audit**: the `audit_as_ritual` trap ("3+ audits without fix → ritual, not process") has officially triggered. Advisory audits have proven insufficient; this gap requires enforcement or an explicit FR to schedule remediation.

3. ⚠ DRIFT (PERSISTENT) — Five consecutive `chore(examples)` commits (spanning three audit windows) form a design arc: filename conventions → ThreadPoolExecutor parallelization → EXIF metadata enrichment with concept/scene_brief fields. No diary entry captures the threading model decision or the metadata-embedding tradeoff. The reasoning is lost to `git log` one-liners. Flagged in audit #140 as well — drift is calcifying into norm.

4. ✓ COMPLIANT — Both `# noqa` suppressions in `yamlgraph/` (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`) are documented in `docs/confessions.md` with CONF-IDs.

5. ✓ COMPLIANT — FR-203 and FR-204 are properly structured feature requests with problem statements, proposed solutions, and scoped effort. Planning before coding (Commandment 1) honoured.

**Heuristic:** Three advisory audits flagging the same gap proves the `detection_without_enforcement` pattern from the Knowledge Graph: "Lint without gate = advisory → add CI block or remove claim." The `audit_as_ritual` trap is now confirmed. The remedy is not a fourth audit — it is either (a) a CI gate that blocks commits touching files with open req-tag gaps, or (b) an FR that schedules the remediation as explicit, trackable work with a deadline. Audit findings that cannot escalate to enforcement are decoration.

**Seed:** Should the Inquisitor auto-create a Feature Request when a violation persists across N audits (the `inquisitor_auto_escalation` seed from the Knowledge Graph)? The threshold (N=3) has been met — what would the FR template look like, and should it carry a priority flag that surfaces in `req_coverage.py --strict`?
