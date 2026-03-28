## 2026-03-15: Inquisitor Audit — Post-FR-202 Map Subgraph Compliance

**Context:** Audited the 5 most recent commits on `main` (`42e5236`..`06b93c4`), with focus on `42e5236` (`feat(map): FR-202 add subgraph support to map nodes`) which landed after audit-133. Assessed Conventional Commits, ADR-001, changelog, diary, and noqa confessions.

**Findings:**

1. ✗ **VIOLATION — Audit-133 applied superseded rule (Co-authored-by).** The previous audit flagged 3 commits for missing `Co-authored-by: Copilot` trailers. However, FR-167 (`remove-copilot-trailer-requirement`, status: Implemented) explicitly retired this requirement — the trailer was removed from `.github/copilot-instructions.md` and enforcement scripts. Audit-133's ✗ VIOLATION was a false positive. The Inquisitor fell into `plausible_wrong_answer` trap: the finding looked correct but applied a superseded rule. **This is the most significant finding** — a false violation erodes audit credibility.

2. ⚠ **DRIFT — Framework feat tagged to example REQ.** `42e5236` modifies core `yamlgraph/map_compiler.py` to support `NodeType.SUBGRAPH` in map iteration — a framework-level capability extension. Tests tag `REQ-YG-198` (image pipeline example), not `REQ-YG-040` (map node compilation) where the actual change lives. The capability is tested and traced, but the req link points downstream instead of at the boundary where the change occurs. Normalizing at the boundary would tag tests to REQ-YG-040.

3. ✓ **COMPLIANT — Conventional Commits.** All 5 commits follow `type(scope): description`. Both `feat` commits reference FR-202/FR-109.

4. ✓ **COMPLIANT — Changelog and diary.** Fragments exist for all feat/fix commits (`feat-map-over-subgraph.md`, `FR-202-image-generation-pipeline.md`, `fr-109-batch-image-prompts.md`, `fix-image-pipeline-dict-prompts.md`). Diary reflections for FR-202 and FR-109 both present with full Context/Trap/Insight/Heuristic/Seed structure.

5. ✓ **COMPLIANT — noqa confessions.** Both active suppressions (`ANN001` in `executor_async.py`, `ARG002` in `token_tracker.py`) have corresponding CONF entries in `docs/confessions.md`.

**Heuristic:** The Inquisitor must verify its own ruleset is current before judging. A superseded requirement still in the auditor's mental model produces `plausible_wrong_answer` in reverse — a plausible violation that is actually a false positive. **Refresh the canon before applying it.** This is `infrastructure_self_exempt` applied to the audit process itself: the tool that enforces doctrine must also obey it.

**Seed:** Should the Inquisitor pipeline include an automated "canon refresh" step that checks `feature-requests/` for any `Status: Implemented` FRs that modify audit rules, ensuring superseded rules are excluded before findings are emitted?
