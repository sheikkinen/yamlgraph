---

## 2026-03-27: Inquisitor Audit — FR Docs & Image Pipeline Chore Batch

**Context:** Audited the 5 most recent commits (72fa12f..e7d8202): two `docs(FR)` adding FR-203 and FR-204 for enforce pipeline, three `chore(examples)` incrementally improving the image pipeline (timestamps, parallelization, extended EXIF metadata). This audit follows immediately after audit #139, which flagged the same `test_image_pipeline.py` req-tag gap.

**Findings:**

1. ✓ COMPLIANT — All 5 commits follow Conventional Commits format (`docs(FR):`, `chore(examples):`). No `feat`/`fix` commits, so changelog fragments and diary-gate CI correctly not triggered.

2. ✓ COMPLIANT — Both `# noqa` suppressions in `yamlgraph/` (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`) remain confessed in `docs/confessions.md` with CONF-IDs.

3. ✗ VIOLATION (PERSISTENT) — **28 of 34 test functions in `tests/unit/test_image_pipeline.py` still lack `@pytest.mark.req` tags.** Audit #139 flagged this identical violation. Commits 9bb772b and e7d8202 both modified this test file — updating test assertions and imports — without adding the missing req tags. Two consecutive audits flagging the same gap meets the `audit_as_ritual` trap threshold: "3+ audits without fix → ritual, not process." One more pass and this becomes an audit ritual rather than actionable enforcement.

4. ⚠ DRIFT — Five consecutive `chore(examples)` commits (spanning this and the prior audit window) form a coherent body of work: filename conventions → parallelization → EXIF metadata enrichment → PromptMetadata dataclass. This is a design arc, not routine maintenance. No diary entry distills the threading decision or the EXIF-vs-sidecar tradeoff, losing the reasoning for future maintainers.

5. ✓ COMPLIANT — FR-203 and FR-204 are well-structured feature requests with clear problem statements, proposed solutions, and scoped effort estimates. Planning before coding (Commandment 1) honoured.

**Heuristic:** When an audit flags a violation and the next batch of commits touches the same file without remediation, the gap calcifies. The `audit_as_ritual` trap is not about the third audit — it is about the second commit to the flagged file that chose not to fix. **Remediation should be gated on file-touch, not audit count:** if a commit modifies a file with known violations, the violations travel with it.

**Seed:** Could a pre-commit hook cross-reference `git diff --name-only` against a machine-readable audit findings file (e.g., `.audit/open-violations.json`) and warn when a flagged file is modified without resolving its open items?
