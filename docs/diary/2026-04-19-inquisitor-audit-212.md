## 2026-04-19: Inquisitor Audit — FR-253 Branch & Recent Merges

**Context:** Audited the 5 most recent commits spanning the in-flight `feat/fr-253-a2a-consumer-to-contrib` branch (2 commits) and the latest 3 merges to `main` (FR-251, FR-252, docs). Checked Conventional Commits, changelog fragments, requirement traceability, test markers, diary entries, and noqa confessions.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow `type(scope): description` format. Both `feat` commits reference their FR number. The `chore` and `docs` commits are correctly typed.

2. ⚠ DRIFT — **Missing `req:` in changelog front-matter**: `changelog/unreleased/fr-253-a2a-consumer-to-contrib.md` omits the `req:` field from its YAML front-matter. The body references `(REQ-YG-253)` in prose, but the `changelog-req-gate` CI check validates the structured `req:` key, not prose mentions. This will likely fail CI on PR creation.

3. ✓ COMPLIANT — **Requirement traceability**: All new tests carry `@pytest.mark.req()` tags (REQ-YG-243, REQ-YG-250, REQ-YG-251). ARCHITECTURE.md capability table and requirements section updated to reflect the a2a_call → contrib migration across 6 REQ entries.

4. ✓ COMPLIANT — **noqa Confessions**: The single new `# noqa: F401` suppression for `check_python_node_variables` in `vulture_whitelist.py` has a corresponding CONF-209 entry in `docs/confessions.md` with sin and penance documented.

5. ✓ COMPLIANT — **Diary entries**: All three FRs (251, 252, 253) have reflection diary entries with cognitive traps, heuristics, and seeds. FR-253's reflection identifies `framework_ceremony_ratio` as a graduated heuristic candidate.

**Heuristic:** **Structured metadata is the contract, prose is commentary.** The `req:` field missing from front-matter while present in prose text is a boundary violation — CI gates parse YAML keys, not markdown body. When a gate checks structured data, ensure the structured field exists; prose references are insufficient.

**Seed:** Could `scripts/aggregate_changelog.py` emit a warning when a changelog fragment body references `REQ-YG-XXX` but the front-matter `req:` field is absent? This would catch the drift at generation time rather than waiting for CI.
