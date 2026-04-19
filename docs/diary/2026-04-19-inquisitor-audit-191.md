## 2026-04-19: Inquisitor Audit — FR-239/240/241 compliance sweep

**Context:** Audited the 5 most recent commits spanning three feature requests: FR-239 (chatterbox multilingual CLI), FR-240 (a2a_call node type), and FR-241 (worktree teardown self-heal). Two are merged to main (#108, #109); FR-241 is in-flight on its feature branch.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits format with correct `type(scope): FR-XXX` structure. Both `feat` PRs include FR references in titles.
- ✓ COMPLIANT — Changelog fragments exist in `changelog/unreleased/` for all three FRs. Each `feat` and `fix` commit has a corresponding fragment.
- ✓ COMPLIANT — Requirements REQ-YG-242 (FR-239), REQ-YG-243 (FR-240), REQ-YG-244 (FR-241) all present in ARCHITECTURE.md. All test files carry matching `@pytest.mark.req()` tags.
- ✓ COMPLIANT — Diary reflections exist for all three FRs, each with Trap/Cure/Heuristic/Seed structure.
- ⚠ DRIFT — Two independent diary entries (FR-239, FR-240) document the identical CAP/REQ-YG ID collision trap. The cure is known ("merge main before committing capability YAML") and both Seeds propose the same automation (`next_cap_id.py`). A recurring trap documented twice without a filed FR to automate it risks becoming audit-as-ritual (trap: `audit_as_ritual`).

**Heuristic:** When two consecutive diary entries name the same trap and propose the same cure, the second entry is evidence the cure should have been filed as an FR after the first. One diary = insight; two diaries = deferred action.

**Seed:** Should the Inquisitor auto-escalate to an FR when the same trap keyword appears in N consecutive diary entries, enforcing the graduation pattern from the Knowledge Graph?
