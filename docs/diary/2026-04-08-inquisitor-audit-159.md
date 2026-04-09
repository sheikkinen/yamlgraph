## 2026-04-08: Inquisitor Audit — Squash Merge Mislabeling

**Context:** Audited the 5 most recent commits (83d0a9f..126fff4) against the Scripture. Focus: Conventional Commits compliance, changelog discipline, requirement traceability, and commit atomicity.

**Findings:**

- ✗ **VIOLATION — `fix(ci)` squash merge bundles a full feature (9718e27, PR #81).** The commit is titled `fix(ci): exclude examples/demos/tests/ from demo-gate check` but carries the entire FR-215 research-agent-demo: 25 files, 739 insertions including a new graph, 5 prompts, tests, capability YAML, and a `type: feat` changelog fragment. This violates `mixed_commits_erode_auditability` (one concern per commit) and mislabels a `feat` as a `fix`, bypassing the commitlint gate that requires `FR-XXX` in feat PR titles. The author's own changelog fragment (`fr-215-research-agent-demo.md`) declares `type: feat`, confirming awareness. The fix was 4 lines; the feature was 735.

- ⚠ **DRIFT — `chore` commit bundles unrelated diary files (f08d4ef).** Adds 2 lines to copilot-instructions alongside 4 diary/reflection files. Low harm since all are docs, but the concern mixing makes `git blame` noisy.

- ✓ **COMPLIANT — All 5 commits follow Conventional Commits syntax.** Types: `docs(FR)` ×3, `chore`, `fix(ci)`.

- ✓ **COMPLIANT — Changelog fragments present for feat and fix work.** Both `fix-ci-demo-gate-tests-exclusion.md` and `fr-215-research-agent-demo.md` exist in `changelog/unreleased/`.

- ✓ **COMPLIANT — Tests tagged with `@pytest.mark.req("REQ-YG-217")`.** REQ-YG-217 confirmed present in ARCHITECTURE.md (2 occurrences). No new `noqa` suppressions. Diary entries written for FR-215 and import-linter reflection.

**Heuristic:**

> In squash-merge workflows, the PR title *is* the commit message. A PR that bundles a feature inside a fix-titled branch bypasses Conventional Commit gates designed to enforce traceability. The gate trusts the label; if the label lies, the gate is blind. Separate PRs for separate concerns — especially when one is `fix` and the other is `feat`.

**Seed:**

Could the `commitlint` CI job cross-check the PR title's `type` against the changelog fragments in the diff? If a PR titled `fix(ci)` contains a `type: feat` changelog fragment, that contradiction should block merge — the label and the evidence disagree.
