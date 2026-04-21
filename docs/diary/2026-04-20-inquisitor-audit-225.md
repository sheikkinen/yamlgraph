## 2026-04-20: Inquisitor Audit — Recent Commits on fix/research-prompt-ecosystem-search

**Context:** Audited the latest 5 commits (2115b81d..eb7fe111) spanning merge housekeeping, FR-258 planning, and the ecosystem-search fix to the Chaplain research prompt. Checked against Conventional Commits, CHANGELOG, ADR-001, diary, and noqa Confessions.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow the format (`chore:`, `chore(chaplain):`, `docs(FR):`, `fix(chaplain):`). Well-scoped types and messages.

2. ✓ **COMPLIANT — CHANGELOG fragment**: `fix(chaplain)` commit (eb7fe111) has a corresponding `changelog/unreleased/research-prompt-ecosystem-search.md` fragment. `docs`/`chore` types correctly omitted.

3. ✓ **COMPLIANT — noqa Confessions**: `noqa_coverage.py` reports 0 undocumented suppressions across 86 total `noqa` markers. All confessed.

4. ✓ **COMPLIANT — ADR-001 req tags**: `test_chaplain_research_step.py` (264 lines, added in eb7fe111) carries 6 `@pytest.mark.req("REQ-YG-260")` annotations. Capability CAP-113 and REQ-YG-260 pre-exist from FR-257.

5. ⚠ **DRIFT — Missing standalone diary for fix commit**: `fix(chaplain): add ecosystem search to research prompt` (eb7fe111) introduced a distinct insight — the research step looked inward (codebase + diary) but not outward (competing frameworks). This is a meaningful cognitive correction (the A2A dedicated node type would have been caught earlier with ecosystem search). The parent FR-257 has a diary entry, but the fix's insight ("outward search catches strategic misclassification") is not distilled anywhere. The diary-gate doesn't trigger because the commit title lacks `FR-XXX`, so CI wouldn't catch this gap.

**Heuristic:** *Follow-up fixes that carry novel insight deserve their own diary entry, not just a changelog fragment.* The diary-gate's FR-XXX title filter creates a blind spot: meaningful fixes without FR references slip through without distillation. The commit message contained the insight, but commit messages are not searchable by the Chaplain's research step — diary entries are.

**Seed:** Should the diary-gate expand its trigger beyond `FR-XXX` references? A heuristic: if a `fix` commit message exceeds N lines (indicating deliberate reasoning, not a one-liner), require a diary entry. Alternatively, the Chaplain research step could search `git log --format='%B'` in addition to `docs/diary/`, making commit-level insights discoverable without duplicating them into diary files.
