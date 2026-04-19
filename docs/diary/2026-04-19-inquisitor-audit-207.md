## 2026-04-19: Inquisitor Audit — FR-247/FR-249/FR-250 compliance sweep

**Context:** Audited the 5 most recent commits on `feat/fr-247-changelog-req-cross-validation-gate` and `main`. Commits span FR-247 (changelog REQ gate), FR-249 (guardrails pattern docs), and FR-250 (a2a server gaps FR document).

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the format (`feat(changelog)`, `docs(patterns)`, `docs(FR)`, `docs(diary)`, `chore(changelog)`). The `feat` commit (de2636f6) correctly references `FR-247`.

2. ✓ COMPLIANT — **Requirement traceability (ADR-001)**: FR-247 added REQ-YG-255 to ARCHITECTURE.md with CAP-108; FR-249 added REQ-YG-254 with CAP-107. All test functions in `test_check_changelog_req.py` and `test_guardrails_pattern_docs.py` carry `@pytest.mark.req` tags matching the correct REQ IDs. The chore commit (250656c1) documents the CAP/REQ renumbering to resolve a collision — proper stewardship.

3. ✓ COMPLIANT — **Changelog fragments**: Both feat-class changes have fragments in `changelog/unreleased/` with valid YAML front-matter including `req:` fields. Docs-only commits (FR-250, diary) correctly omit fragments since the changelog-gate only requires them for `feat`/`fix`.

4. ✓ COMPLIANT — **Diary entries**: FR-247 has `2026-04-20-reflection-fr-247-changelog-req-cross-validation-gate.md` with heuristic and seed. FR-249 has `2026-04-19-reflection-fr-249.md`. Both follow the reflection template.

5. ⚠ DRIFT — **Commit type vs changelog type mismatch (FR-249)**: Commit `eb2dd983` uses type `docs(patterns)` but the changelog fragment declares `type: feat`. The changelog-gate and diary-gate only fire for `feat`/`fix` PRs — this PR sidestepped both gates by using `docs` as the commit type while still claiming `feat` status in the changelog. No enforcement gap was exploited (diary and fragment both exist), but the asymmetry means a future `docs` PR could smuggle a `feat` changelog entry without triggering the diary-gate.

**Heuristic:** **Changelog type should match commit type at the gate boundary.** When the CI gate keys on the PR title type (`docs` vs `feat`) but the changelog fragment independently declares its own type, a misalignment can bypass enforcement. The `changelog-gate` should cross-check: if a fragment declares `type: feat`, the PR title must also be `feat` (or at minimum, the diary-gate should fire).

**Seed:** Could `commitlint.yml` add a check that validates consistency between the PR title type and any changelog fragment `type:` field? A `docs` PR with a `feat` changelog fragment would be flagged, forcing the author to choose one classification and accept the corresponding gates.
