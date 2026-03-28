## 2026-03-15: Inquisitor Audit — Post-FR-202 Fix-Up Chain

**Context:** Audited the 5 most recent commits on `main` (d118bc8–e01eb18), all post-merge follow-ups to the FR-202 image generation pipeline PR (#66). Prior audit (136) flagged direct pushes and missing trailers on 4 of these; this audit adds commit `e01eb18` and re-evaluates the pattern.

**Findings:**

1. ✗ VIOLATION — **Direct pushes to `main` continue.** Commit `e01eb18` (`chore(examples): parallelize image generation`) is the 5th consecutive direct push after PR #66's squash merge. No break-glass entry in `reference/break-glass.md`. Branch protection requires PRs — this is either admin bypass without documentation or protection not yet enforced on this branch. Audit 136 flagged the same issue; no corrective action observed.

2. ✗ VIOLATION — **Co-authored-by trailers absent on all 5 commits.** Scripture requires `Co-authored-by: Copilot <...>` on every commit. Zero of the five carry the trailer. Repeat finding from audit 136 — now a pattern, not an incident.

3. ✓ COMPLIANT — **Conventional Commits and changelog fragments.** All 5 commits follow `type(scope): description`. The `feat` commit references `FR-202`. Both `fix` commits and the `feat` commit have corresponding fragments in `changelog/unreleased/`. `chore` commits correctly omit fragments.

4. ✓ COMPLIANT — **Requirement traceability (ADR-001).** All 6 test classes in `test_image_pipeline.py` carry `@pytest.mark.req("REQ-YG-198")`. Both `noqa` suppressions in `yamlgraph/` (ANN001, ARG002) are documented with CONF-IDs in `docs/confessions.md`.

5. ⚠ DRIFT — **`feat-map-over-subgraph.md` fragment omits `req:` field.** The `feat(map)` commit added a new capability (map-over-subgraph) to core `map_compiler.py` but the changelog fragment has no `req:` reference. The capability reuses `REQ-YG-198` from the parent FR-202, which is defensible — but a distinct REQ for subgraph-in-map would improve traceability.

**Heuristic:** When the same violation appears in consecutive audits without corrective action, it has graduated from incident to systemic gap. Escalate: either enforce the gate (pre-push hook, CI check) or amend the doctrine to acknowledge the exception. An audit that finds the same defect twice without triggering a fix is ritual, not process (trap: `audit_as_ritual`).

**Seed:** Should repeated audit violations auto-generate a Feature Request via the Chaplain inbox, closing the loop between detection and enforcement?
