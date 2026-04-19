## 2026-04-19: Inquisitor Audit — FR-240/FR-241 branch compliance

**Context:** Audited the latest 5 commits on `feat/fr-241-complete-worktree-teardown-self-heal`, covering FR-240 (a2a_call node), FR-241 (worktree teardown), and supporting chore/docs commits. Checked Conventional Commits, changelog fragments, ADR-001 traceability, noqa confessions, and diary reflections.

**Findings:**

1. ✓ COMPLIANT — `feat(graph): FR-240 add a2a_call node type (#109)`: Conventional Commit format correct; changelog fragment `fr-240-a2a-call-node-type.md` present; REQ-YG-243 added to ARCHITECTURE.md; all tests tagged `@pytest.mark.req("REQ-YG-243")`; diary reflection written; new CONF-001 documented; demo-output.log included.

2. ✓ COMPLIANT — `fix(worktree): FR-241 complete teardown self-heal`: Conventional Commit format correct; changelog fragment `fr-241-worktree-teardown-self-heal.md` present; REQ-YG-242 added; tests tagged `@pytest.mark.req("REQ-YG-241")`; new noqa (S603, S607) documented as CONF-045/CONF-046.

3. ✓ COMPLIANT — `chore: merge main + fix CAP-100→102, REQ-YG-242→244 to avoid collision (FR-241)`: Conventional Commit format; housekeeping commit resolving ID collisions after merge — no new capability, no changelog needed.

4. ✓ COMPLIANT — `chore(diary): reflection on FR-241 worktree teardown and recurring CAP collision`: Diary entry written with trap, cure, heuristic, and seed. Sermon: Distill fulfilled.

5. ⚠ DRIFT — REQ-YG mismatch in FR-241 tests: worktree teardown tests are tagged `@pytest.mark.req("REQ-YG-241")` but ARCHITECTURE.md assigns REQ-YG-242 to the worktree teardown capability (CAP-102). The tests should reference `REQ-YG-242`. The REQ-YG-241 requirement covers pipeline accumulated state (FR-238), not worktree self-heal.

**Heuristic:** When CAP/REQ-YG IDs are renumbered to resolve collisions (as in the merge commit), grep the entire branch for stale references — test `@pytest.mark.req` tags are the most likely to be missed because they live outside ARCHITECTURE.md.

**Seed:** Could `scripts/req_coverage.py --strict` cross-check that each test's `@pytest.mark.req` tag maps to a requirement whose description matches the test file's domain, catching semantic mismatches beyond mere existence?
