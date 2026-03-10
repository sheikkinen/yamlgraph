## 2026-03-10: Inquisitor Audit — chore loophole; anonymous authorship now inert

**Context:** Audited the 5 most recent commits on `main` (11f024e..5732bb7). Window contains 1 `chore(traceability)`, 2 `docs(FR)`, 2 `fix`. Prior audit-86 flagged CHANGELOG erasure and anonymous authorship as recurrent violations.

**Findings:**

1. ✗ VIOLATION (recurrent x6) — All 5 commits authored by `test@test.com`. Flagged in audits 82–86 with zero remediation. Per Scripture trap `audit_as_ritual`: "3+ audits without fix → ritual, not process." This finding is now inert without a blocking gate. Further diary-only flagging is noise.

2. ⚠ DRIFT — `5732bb7` (`chore(traceability): FR-177`) removes CAP-52, REQ-YG-150, and its test file but has no CHANGELOG entry under `[Unreleased]`. Commandment 10: "let the CHANGELOG bear witness." Capability removal is a notable change that deserves a record under `### Removed`.

3. ⚠ DRIFT — FR-177 is a substantive change (removing infrastructure) committed as `chore` type with FR reference, bypassing the diary-gate CI which only checks `feat`/`fix` types. This creates a loophole: reclassify work as `chore` to avoid diary obligation. Same structural gap as non-FR fixes flagged in audit-85/86.

4. ✓ COMPLIANT — All 5 commits follow Conventional Commits format. Allowed types (`chore`, `docs`, `fix`) used correctly with proper scopes. Commandment 10 satisfied for message format.

5. ✓ COMPLIANT — All `@pytest.mark.req` tags present on touched test files (11, 6, 7 tags respectively). Both `# noqa` suppressions (ANN001, ARG002) confessed in `docs/confessions.md`. ADR-001 intact.

**Heuristic:** When a CI gate checks only specific commit types (`feat`/`fix`), substantive changes can bypass enforcement by using a different type (`chore`, `refactor`). Gates should trigger on the *presence of an FR reference* regardless of commit type — `FR-XXX` in the message is the signal that reflection is warranted, not the Conventional Commits prefix.

**Seed:** Should diary-gate trigger on any PR whose title contains `FR-XXX`, regardless of the Conventional Commits type prefix — closing the chore/refactor/perf loophole?
