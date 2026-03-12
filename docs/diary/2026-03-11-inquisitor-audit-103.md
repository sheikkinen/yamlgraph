## 2026-03-11: Inquisitor Audit — REQ-YG-183 gap persists, test relocation risk

**Context:** Audited commits 63efa84..54e7a7e (5 commits: refactor(tests), feat FR-183/184, fix FR-181, docs FR-170, docs FR-184). Follow-up to audit-102 which flagged REQ-YG-183 as missing.

**Findings:**

1. ✗ VIOLATION — **REQ-YG-183 still absent**: Audit-102 flagged that FR-183 (enforce pipeline simplification) ships tests, changelog, and a new 4-node graph topology but has no REQ-YG-183 in `ARCHITECTURE.md`, no capability YAML, and `test_enforce_simplify.py` uses generic tags (REQ-YG-001, REQ-YG-012). One commit later (63efa84), this remains unaddressed. The `req_coverage.py` report shows 119/119 only because REQ-YG-183 was never registered — the gap is invisible to tooling.

2. ⚠ DRIFT — **REQ-YG-083 coverage reduced**: Commit 63efa84 deleted `tests/unit/test_probe_recap.py` (15 `@pytest.mark.req("REQ-YG-083")` tests, 206 lines). Commit message claims coverage survives via `test_thinking_budget.py` and outcaller's own repo. Cross-repo coverage claims are unverifiable by `req_coverage.py` — if outcaller tests break, this repo's traceability report stays green.

3. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the format. `feat` commits include FR-XXX references. `docs` and `refactor` commits are correctly scoped.

4. ✓ COMPLIANT — **Changelog and diary**: FR-183, FR-184, FR-181 all have changelog fragments in `changelog/unreleased/`. Diary reflections exist for FR-183/184 (with Trap/Heuristic/Seed) and FR-181. `docs`-type commits correctly omit fragments.

5. ⚠ DRIFT — **Audit bundled as refactor diary**: Commit 63efa84 (refactor) includes `inquisitor-audit-102.md` as its diary entry rather than a reflection on the test relocation decision. The refactor's reasoning (test pollution, ownership boundaries) is captured only in the commit message, not in a structured diary with Trap/Heuristic/Seed.

**Heuristic:** When an audit flags a violation, the next commit touching the same scope should address it — or explicitly defer with a tracked reason. An unfixed violation that survives across commits is not drift; it is accumulating debt that tooling cannot see.

**Seed:** Should `req_coverage.py --strict` cross-reference `changelog/unreleased/` fragments against `ARCHITECTURE.md` requirements, flagging any FR-XXX changelog entry whose corresponding REQ-YG-XXX is absent?
