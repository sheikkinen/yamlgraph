## 2026-05-22: Inquisitor Audit — v0.5.3 release batch (FR-437, FR-444, FR-445)

**Context:** Audited the 5 most recent commits on `main`: `chore: process overview`, `feat(tools): FR-445`, `feat(graph-loader): FR-444`, `chore(release): v0.5.3 changelog freeze`, and `feat(fsm): FR-437`. These span Python tool path confinement, strict tool load mode, FSM UI log bridge, a release freeze, and documentation.

**Findings:**

1. ✓ COMPLIANT — All 5 commits follow Conventional Commits. The three `feat` commits include `type(scope): FR-XXX` references; both `chore` commits use correct type. Changelog fragments exist for all `feat` PRs (FR-437 frozen to `changelog/0.5.3/`, FR-444 and FR-445 in `changelog/unreleased/`). Diary reflections present for all three FRs.

2. ✓ COMPLIANT — ADR-001 traceability fully observed. FR-444 added CAP-157 with REQ-YG-420–421 and 4 tests correctly tagged. FR-445 tests tag REQ-YG-196 (Portable Chaplain / PythonToolConfig path loading), the correct parent requirement covering graph-root confinement. FR-437 tests tag REQ-YG-319 (FSM bridge shared module) at class level covering all 4 methods.

3. ✓ COMPLIANT — The sole `# noqa: S603` in `yamlgraph/utils/fsm/ui_log.py` (FR-437) is documented as CONF-255 in `docs/confessions.md`. No new unconfessed suppressions introduced by any of the 5 commits.

4. ⚠ DRIFT — 52 pre-existing `# noqa` suppressions across `yamlgraph/` and `scripts/` lack `CONF-XXX` entries. Count grew from 28 (last audit) to 52, suggesting either new unconfessed additions in older commits or a prior undercount. This debt accumulates interest: each unaudited suppression is a potential hidden rule violation.

5. ⚠ DRIFT — FR-445 added CAP-155 (Schema Loader Tool Type, REQ-YG-417–418) in ARCHITECTURE.md but the FR-445 tests themselves tag REQ-YG-196, not REQ-YG-417/418. This is correct (FR-445 extends the PythonToolConfig path loading, not the schema loader), but the capability table entry for CAP-155 listing `python_tool.py` in its module column creates ambiguity — two capabilities claim the same file for different concerns. Not a violation, but a traceability smell.

**Heuristic:** When a single source file serves two capabilities (REQ-YG-196 for path-based loading, REQ-YG-417 for schema loader integration), the capability registry should disambiguate by listing only the functions or classes within that file, not the file itself. File-level granularity invites false ownership claims.

**Seed:** Should the noqa confession debt (now 52 entries) trigger an automated FR via the Inquisitor auto-escalation seed — or does the recurring audit finding without remediation prove the `audit_as_ritual` trap is active, and a CI gate blocking PRs with unconfessed noqa is the only cure?
