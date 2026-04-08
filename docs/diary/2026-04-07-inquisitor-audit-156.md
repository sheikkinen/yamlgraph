## 2026-04-07: Inquisitor Audit — Post FR-215 Enforcement (126fff4..019fc86)

**Context:** Fifth audit today. Covers the 5 most recent commits on `feat/fr-215-research-agent-demo`: the FR-215 enforcement commit (019fc86), FR-215 feature request filing (126fff4), image pipeline batch (34e0920), and the 0.4.66 release pair (8fc47ae, 877bb2c). Checked Conventional Commits, changelog fragments, ADR-001 requirement traceability, diary entries, noqa confessions, and Sermon compliance.

**Findings:**

1. ✗ **VIOLATION** — Commit 019fc86 (`fix(ci): exclude examples/demos/tests/ from demo-gate check`) bundles **25 files** across 5+ unrelated concerns: the CI fix (1 file), the entire FR-215 demo (graph, prompts, README, demo-output.log — 8 files), capability + ARCHITECTURE.md + changelog fragments (4 files), test file (1 file), feature requests (2 files), and 6 diary entries. The commit message describes only the CI fix. This is the `mixed_commits_erode_auditability` antipattern at escalated severity — the title now actively misrepresents the commit's scope. A `fix(ci):` commit should contain only the CI change; the FR-215 demo should be a separate `feat(demos): FR-215 ...` commit.

2. ⚠ **DRIFT** — FR-215 has `Status: Implemented` but no `## Judgement` section. This is the 5th audit (153, 154, 155, 156) flagging missing Judgement records. The Sermon requires Plan → **Judge** → Enforce; when judgement is unrecorded, the Enforce step has no frozen scope to obey.

3. ✓ **COMPLIANT** — ADR-001 traceability for FR-215 is complete: REQ-YG-217 added to ARCHITECTURE.md, CAP-83 capability file created, all 5 tests in `test_research_agent_demo.py` tagged with `@pytest.mark.req("REQ-YG-217")`.

4. ✓ **COMPLIANT** — All noqa suppressions in `yamlgraph/` (ANN001, ARG002) are documented in `docs/confessions.md`. Zero undocumented suppressions.

5. ✓ **COMPLIANT** — Diary reflection exists for FR-215 (`2026-04-07-reflection-fr-215-research-agent-demo.md`). Identifies the `infrastructure_self_exempt` trap and extracts the "boundary exclusions need explicit allowlists" heuristic. Seed planted.

**Heuristic:** When a commit message describes concern A but ships concerns A through E, the commit message becomes a lie — and `git log --oneline` becomes an unreliable audit trail. The `mixed_commits_erode_auditability` trap has now survived **5 consecutive audits** (152–156). Detection without enforcement is ritual, not process. The structural gate proposed in audit-155 (max file-diversity-per-commit) remains unimplemented. Until that gate exists, every audit that flags this violation without escalating to an FR is itself complicit in the `audit_as_ritual` trap.

**Seed:** Should audit-156's finding #1 be escalated to a formal FR requiring a pre-commit hook that rejects commits touching more than N unrelated top-level paths — breaking the cycle where audits detect but never enforce the mixed-commit antipattern?
