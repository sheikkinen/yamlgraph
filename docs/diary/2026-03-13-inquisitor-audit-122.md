## 2026-03-13: Inquisitor Audit — Pipeline Self-Exemption Crystallizes

**Context:** Audit of the 5 most recent commits (ab9dae3..ce4292c) against the Scripture. Covers two `feat` PRs (FR-192, FR-193) and three machine-generated `docs(FR)` pipeline artifacts (FR-194, FR-195, FR-196).

**Findings:**

1. ✓ **COMPLIANT — feat commits follow full doctrine.** Both `feat` commits (FR-192 `ab9dae3`, FR-193 `ce73716`) satisfy all gates: Conventional Commits with `FR-XXX` references, changelog fragments in `changelog/unreleased/`, `@pytest.mark.req` tags on all tests (REQ-YG-188..192), diary reflections committed with their PRs, ARCHITECTURE.md updated, Copilot co-author trailer present. The mechanical gates hold.

2. ✗ **VIOLATION — Enforce pipeline pushes directly to main without PR.** Three `docs(FR)` commits (ce4292c, 30c9760, 78c2844) lack PR numbers in their messages — no `(#XX)` suffix. Branch protection requires pull requests (documented in CLAUDE.md). The enforce pipeline bypasses this gate. This is the `infrastructure_self_exempt` trap made concrete: "Meta-tooling exempted from gates it enforces → apply same rules to the guardrail as to what it guards."

3. ⚠ **DRIFT — Bot identity `Test <test@test.com>` now on 3 of 5 commits (4th consecutive audit).** Audits #120 and #121 flagged this. No FR created, no enforcement action taken. Per the `audit_as_ritual` trap: "3+ audits without fix → ritual, not process." This finding has now appeared in 3+ audits — it must be escalated to a mandatory FR per the heuristic from audit #121.

4. ⚠ **DRIFT — 14 uncommitted diary/audit files accumulating.** Same backlog identified in audit #121. The pipeline produces artifacts faster than it commits them. The `process_cost_inversion` pattern continues: introspective apparatus generates more entropy about gaps than the gaps themselves contain.

5. ✓ **COMPLIANT — noqa confessions, req coverage, changelog fragments.** Both `ANN001` and `ARG002` suppressions documented in `docs/confessions.md`. All test functions carry `@pytest.mark.req` tags. No undocumented noqa found.

**Heuristic:** **Infrastructure must obey its own rules.** When the enforce pipeline pushes directly to `main` while branch protection mandates PRs, the pipeline invalidates the very gate it claims to enforce. The `automation_inherits_doctrine` cure is explicit: "Scripts follow same rules as humans → no --no-verify bypass." A direct push is `--no-verify` at the git level. The pipeline must create a PR branch, push there, and let CI + branch protection validate — even for `docs(FR)` commits.

**Seed:** Should the enforce pipeline's direct-push bypass be the first target for FR-196 (portable chaplain), or does it warrant its own FR? A `docs(FR)` commit that fails CI would currently land on `main` unchecked — what is the blast radius of a malformed FR file that breaks a linter or pre-commit hook?
