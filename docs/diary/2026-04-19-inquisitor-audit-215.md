## 2026-04-19: Inquisitor Audit — FR-254, FR-253, FR-251

**Context:** Audited the 5 most recent commits spanning three feature requests (FR-254 diary-index graph, FR-253 a2a-consumer-to-contrib, FR-251 harden-remote-inbox) plus their planning and reflection commits. Checked Conventional Commits, changelog fragments, ARCHITECTURE.md requirements, test req tags, diary reflections, and noqa confessions.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow `type(scope): FR-XXX description` format. Planning (`docs(FR):`), implementation (`feat(diary):`, `feat(a2a):`, `feat(chaplain):`), and reflection (`docs(diary):`) all correctly typed.

2. ✓ COMPLIANT — **ADR-001 Requirement Traceability**: FR-254 added CAP-110/REQ-YG-257 to ARCHITECTURE.md with 19 `@pytest.mark.req("REQ-YG-257")` tagged tests. FR-253 carried 89 req tags. FR-251 carried 8 req tags. No untagged test functions found in new code.

3. ✓ COMPLIANT — **Diary Reflections**: All three feat FRs have diary entries with traps, heuristics, and seeds. FR-254's reflection identifies recursive self-analysis risk. FR-253's reflection extracts `framework_ceremony_ratio` heuristic. FR-251's diary shipped with its merge commit.

4. ⚠ DRIFT — **noqa Cross-Reference**: `vulture_whitelist.py:252` has `# noqa: F401 (API stub for FR-252 compat)` while every other suppression in that file uses `(CONF-XXX)` format. The confession exists (CONF-209 in `docs/confessions.md`) but the inline comment doesn't reference it. The chain is intact but the link is misformatted.

5. ✓ COMPLIANT — **Changelog Fragments**: All three feat FRs have fragments in `changelog/unreleased/` with correct YAML front-matter (`type: feat`, `req: REQ-YG-XXX`). Generated changelog correctly aggregates them.

**Heuristic:** **noqa-confession cross-reference is a two-point contract** — the confession file documents the sin, and the inline comment must cite the CONF-XXX ID. When either end breaks, the traceability chain becomes grep-hostile. A pre-commit check matching `# noqa:` lines against `(CONF-\d+)` patterns would catch format drift mechanically.

**Seed:** Could `scripts/req_coverage.py` be extended (or a sibling `scripts/noqa_coverage.py` created) to verify every `# noqa` inline comment in tracked Python files references a valid CONF-XXX entry in `docs/confessions.md`? This would graduate the noqa confession contract from advisory to enforced.
