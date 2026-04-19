## 2026-04-19: Inquisitor Audit — FR-254/255 Feature Commits and FR-256/257 Planning Docs

**Context:** Audited the latest 5 commits on `main` (c2f79058..bdfb5faa) covering two feature implementations (FR-254 diary-index graph, FR-255 extract shared invoke_graph) and three planning docs (FR-254/256/257). Cross-referenced against Conventional Commits, changelog fragments, ADR-001 requirement traceability, diary reflections, and noqa confessions.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits format (`feat(scope): FR-XXX ...` for features, `docs(FR): ...` for planning docs). PR numbers present on feat commits.
- ✓ COMPLIANT — Both feat commits (FR-254, FR-255) have changelog fragments in `changelog/unreleased/`. Requirements REQ-YG-257 and REQ-YG-258 added to `ARCHITECTURE.md`. All new tests carry `@pytest.mark.req()` tags (10 in `test_diary_index.py`, 6 in `test_invoke_graph.py`).
- ✓ COMPLIANT — Diary reflections exist for both features: `2026-04-20-reflection-fr-254-diary-index-graph.md` and `2026-04-19-reflection-fr-255-extract-shared-invoke-graph.md`. Both contain Heuristic and Seed sections per Sermon.
- ✓ COMPLIANT — All 21 `# noqa` suppressions in `yamlgraph/` have corresponding CONF-XXX entries in `docs/confessions.md`. One inline reference (CONF-004 in `a2a_server.py`), rest documented by file path and line number.
- ⚠ DRIFT — `docs/confessions.md` has three entries for the same `check_state_declarations` suppression (CONF-001 at L109, CONF-008 at L106, CONF-044 at L108) — line numbers drifted across edits. Only one actual `# noqa` exists. Stale entries should be pruned; consider adding a `scripts/noqa_coverage.py` check for orphaned CONF entries.

**Heuristic:** **confession_drift** — When code is refactored, `# noqa` lines shift but confession entries keep their original line numbers, creating phantom duplicates. A cross-validation script (noqa line → CONF-ID → file:line) would catch staleness mechanically, same way `check_changelog_req.py` catches phantom REQs.

**Seed:** Could `scripts/noqa_coverage.py` be extended to detect orphaned CONF entries — confessions that reference file:line combinations where no `# noqa` actually exists? This would enforce confession hygiene at CI, preventing the kind of drift observed in CONF-001/008/044.
