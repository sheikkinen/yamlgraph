## 2026-03-15: Inquisitor Audit — FR-202 image pipeline & follow-up commits

**Context:** Audited the 5 most recent commits (42e5236–9bb772b) spanning `feat(map): FR-202`, `fix(examples): EXIF metadata`, and 3 `chore(examples)` polish commits. Checked Conventional Commits, changelog fragments, requirement traceability (ADR-001), test tagging, diary coverage, and noqa confessions.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits: `feat(map)`, `fix(examples)`, `chore(examples)` ×3. The `feat` commit carries `FR-202` reference as required.
- ✓ COMPLIANT — Changelog fragments present for both `feat` (`feat-map-over-subgraph.md`) and `fix` (`fix-exif-only-metadata.md`). Chore commits correctly omit fragments per convention.
- ✓ COMPLIANT — Requirement traceability complete: REQ-YG-198 registered in `ARCHITECTURE.md`, capability `CAP-77-image-generation-pipeline.yaml` exists, and all 6 test functions in `test_image_pipeline.py` carry `@pytest.mark.req("REQ-YG-198")`.
- ✓ COMPLIANT — Both `noqa` suppressions in production code (ANN001, ARG002) are documented in `docs/confessions.md` with CONF-XXX entries.
- ✓ COMPLIANT — Diary entry `2026-03-15-reflection-fr-202.md` covers the FR-202 feature with full template: Context, Trap Avoided (intent_drift), Insight (detection→enforcement graduation), Heuristic (3-file coupling), and Seed (auto-detect missing CAP entries).

**Heuristic:** A clean audit after a multi-commit feature sequence signals the gates are working — the req_coverage script, changelog-gate, and diary-gate form a triple-lock that catches omissions at different granularities. When all three pass, the remaining risk is semantic correctness, not process compliance.

**Seed:** The triple-lock (req_coverage + changelog-gate + diary-gate) catches omissions but not staleness. Could a "freshness check" detect when a capability YAML or requirement description drifts from the code it documents — e.g., REQ-YG-198's description still says "sidecar .txt files" after the EXIF-first fix changed that behavior?
