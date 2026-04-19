## 2026-04-19: Inquisitor Audit — Changelog REQ Cross-Wiring Widens After Renumber

**Context:** Audited the 5 most recent commits (cac26a7f..cad50cfa) spanning FR-032 node-level caching, FR-237 Chatterbox consolidation, FR-238 pipeline accumulated state docs, and FR-237 race/pipeline docs. This is the 7th audit cycle observing the FR-234 changelog REQ cross-wiring first identified in audit-171.

**Findings:**

1. ✗ **VIOLATION — 4 changelog fragments cross-wired after renumber.** The merge commit `0f967558` renumbered CAP/REQ in ARCHITECTURE.md and test files but left changelog fragments untouched. Result: `fr-032-node-level-caching.md` says `req: REQ-YG-032` (CLI entry point) instead of `REQ-YG-239` (node-level cache); `fr-234-parallel-fan-out-edges.md` says `REQ-YG-235` instead of `REQ-YG-237`; `fr-235-compile-time-pipeline-templates.md` says `REQ-YG-235` instead of `REQ-YG-236`; `fr-238-pipeline-accumulated-state.md` says `REQ-YG-238` instead of `REQ-YG-241`. The `partial_remediation` trap at scale: renumber touched ARCHITECTURE.md and tests but skipped the changelog boundary entirely.

2. ✗ **VIOLATION — FR-234 cross-wiring survives 7th cycle.** First identified in audit-171, the `fr-234-parallel-fan-out-edges.md` → `REQ-YG-235` mismatch has been observed in every audit since. The `audit_as_ritual` trap remains structurally locked: the Inquisitor's diary-only write scope cannot deposit `.chaplain/inbox/` escalation artifacts.

3. ✓ **COMPLIANT — Conventional Commits, test traceability, diary reflections.** All 5 commits follow Conventional Commits. `feat` commit (`0073b3f5`) includes FR reference. Cache tests tagged `REQ-YG-239` (10 tests). Chatterbox tests tagged `REQ-YG-234`, `REQ-YG-235`, `REQ-YG-238`. Both FR-032 and FR-237 have diary reflections with cognitive traps and seeds.

4. ✓ **COMPLIANT — noqa confessions.** All 19 `# noqa` suppressions in `yamlgraph/` have corresponding CONF-XXX entries in `docs/confessions.md`. No new unsuppressed noqa added in audited range.

5. ⚠ **DRIFT — FR-237 changelog front matter lists single req.** `fr-237-chatterbox-consolidate-and-cli.md` has `req: REQ-YG-235` in front matter but the body text references both `REQ-YG-235` and `REQ-YG-238`. The speak CLI (REQ-YG-238) is a distinct capability not captured in the front matter field. Minor — the body text is accurate, but CI tooling that reads only front matter will miss the second requirement.

**Heuristic:** A renumber operation is a boundary-crossing change: it must touch every artifact type that references the old identifier (ARCHITECTURE.md, tests, changelog fragments, capability YAML, feature requests). A post-renumber `grep -r "REQ-YG-OLD"` across the entire repo — not just the files that come to mind — is the minimum verification. The cheapest enforcement: a CI script that cross-checks changelog `req:` front matter against ARCHITECTURE.md requirement definitions.

**Seed:** Should the renumber operation itself be a scripted tool (`scripts/renumber_req.py OLD NEW`) that atomically updates all artifact boundaries, rather than a manual grep-and-fix that invites `partial_remediation`?
